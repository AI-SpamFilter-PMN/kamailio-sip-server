import os
import time
import json
import logging
from datetime import datetime

import requests
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

RECORDINGS_DIR = os.getenv(
    "RECORDINGS_DIR",
    "/var/spool/freeswitch/recordings"
)

TRANSCRIPTS_DIR = os.getenv(
    "TRANSCRIPTS_DIR",
    "/app/transcripts"
)

HOST_PROJECT_DIR = os.getenv("HOST_PROJECT_DIR", "")

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "nova-3")
LANGUAGE = os.getenv("DEEPGRAM_LANGUAGE", "ar")
DATABASE_URL = os.getenv("DATABASE_URL")

os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

if not DEEPGRAM_API_KEY:
    logging.error("DEEPGRAM_API_KEY is not configured.")
    raise SystemExit(1)


def get_db_connection():
    if not DATABASE_URL:
        logging.warning("DATABASE_URL is not configured.")
        return None

    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to PostgreSQL: {e}")
        return None


def parse_filename_metadata(wav_filename):
    try:
        base_name = os.path.splitext(wav_filename)[0]
        parts = base_name.split("_")

        date_str = parts[0]
        source = parts[1]
        destination = parts[3]

        started_at = datetime.strptime(
            date_str,
            "%Y-%m-%d-%H-%M-%S"
        )

        return started_at, source, destination

    except Exception as e:
        logging.error(
            f"Error parsing filename {wav_filename}: {e}"
        )

        return datetime.utcnow(), "UNKNOWN", "UNKNOWN"


def save_call_to_neon(
    wav_filename,
    full_transcript,
    host_wav_path
):
    conn = get_db_connection()

    if not conn:
        return

    started_at, source, destination = parse_filename_metadata(
        wav_filename
    )

    ended_at = datetime.utcnow()

    query = """
        INSERT INTO calls (
            source,
            destination,
            started_at,
            ended_at,
            status,
            transcript,
            recording_path
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    source,
                    destination,
                    started_at,
                    ended_at,
                    "COMPLETED",
                    full_transcript,
                    host_wav_path
                )
            )

            inserted_id = cur.fetchone()[0]
            conn.commit()

            logging.info(
                f"SUCCESS: Inserted call record with ID: {inserted_id}"
            )

    except Exception as e:
        conn.rollback()
        logging.error(
            f"Error inserting record into PostgreSQL: {e}"
        )

    finally:
        conn.close()


def transcribe_wav(wav_path):
    url = "https://api.deepgram.com/v1/listen"

    params = {
        "model": DEEPGRAM_MODEL,
        "language": LANGUAGE,
        "smart_format": "true",
        "punctuate": "true",
    }

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/wav",
    }

    with open(wav_path, "rb") as f:
        audio_data = f.read()

    try:
        response = requests.post(
            url,
            params=params,
            headers=headers,
            data=audio_data,
            timeout=60
        )

        response.raise_for_status()

        result = response.json()

        transcript = (
            result["results"]
            ["channels"][0]
            ["alternatives"][0]
            ["transcript"]
        )

        confidence = (
            result["results"]
            ["channels"][0]
            ["alternatives"][0]
            .get("confidence")
        )

        return {
            "transcript": transcript,
            "confidence": confidence,
            "raw": result
        }

    except requests.exceptions.RequestException as e:
        logging.error(
            f"Deepgram API request failed: {e}"
        )

        if hasattr(e, "response") and e.response is not None:
            logging.error(
                f"Response body: {e.response.text}"
            )

        return None

    except (KeyError, IndexError) as e:
        logging.error(
            f"Unexpected Deepgram response structure: {e}"
        )

        return None


def process_file(wav_filename):
    wav_path = os.path.join(
        RECORDINGS_DIR,
        wav_filename
    )

    json_filename = wav_filename.replace(
        ".wav",
        ".json"
    )

    json_output_path = os.path.join(
        TRANSCRIPTS_DIR,
        json_filename
    )

    host_wav_path = os.path.join(
        HOST_PROJECT_DIR,
        "recordings",
        wav_filename
    )

    logging.info(
        f"PROCESSING WITH DEEPGRAM: {wav_filename}"
    )

    start_time = time.time()

    result = transcribe_wav(wav_path)

    elapsed = round(
        time.time() - start_time,
        2
    )

    if result:
        output_data = {
            "wav_file": wav_filename,
            "processed_at": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "processing_seconds": elapsed,
            "model": f"deepgram-{DEEPGRAM_MODEL}",
            "transcript": result["transcript"],
            "confidence": result["confidence"],
        }

        with open(
            json_output_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                output_data,
                f,
                ensure_ascii=False,
                indent=4
            )

        logging.info(
            f"SUCCESS: Saved transcript to "
            f"{json_output_path} "
            f"(took {elapsed}s)"
        )

        logging.info(
            f"Result: {result['transcript']}"
        )

        save_call_to_neon(
            wav_filename,
            result["transcript"],
            host_wav_path
        )

    else:
        logging.error(
            f"FAILED: Could not transcribe {wav_filename}"
        )


if __name__ == "__main__":
    logging.info(
        f"Starting Deepgram Transcriber "
        f"({DEEPGRAM_MODEL}, lang={LANGUAGE}). "
        f"Watching: {RECORDINGS_DIR}"
    )

    while True:
        try:
            if os.path.exists(RECORDINGS_DIR):
                for file_name in os.listdir(
                    RECORDINGS_DIR
                ):
                    if not file_name.endswith(".wav"):
                        continue

                    json_filename = file_name.replace(
                        ".wav",
                        ".json"
                    )

                    json_output_path = os.path.join(
                        TRANSCRIPTS_DIR,
                        json_filename
                    )

                    if os.path.exists(
                        json_output_path
                    ):
                        continue

                    wav_path = os.path.join(
                        RECORDINGS_DIR,
                        file_name
                    )

                    last_size = -1
                    stable_counter = 0

                    while stable_counter < 3:
                        if not os.path.exists(
                            wav_path
                        ):
                            break

                        current_size = os.path.getsize(
                            wav_path
                        )

                        if (
                            current_size > 1000
                            and current_size == last_size
                        ):
                            stable_counter += 1
                        else:
                            stable_counter = 0

                        last_size = current_size

                        time.sleep(1)

                    if (
                        os.path.exists(wav_path)
                        and stable_counter >= 3
                    ):
                        process_file(file_name)

        except Exception as e:
            logging.error(
                f"Error in main loop: {e}"
            )

        time.sleep(2)