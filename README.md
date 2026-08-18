# Kamailio Lab

Docker-based VoIP lab using Kamailio, FreeSWITCH, RTPengine, PostgreSQL, and Deepgram.

## Project Structure

```text
kamailio-lab/
├── Dockerfile.freeswitch
├── Dockerfile.kamailio
├── Dockerfile.transcriber_deepgram
├── docker-compose.yml
├── docker-entrypoint-freeswitch.sh
├── docker-entrypoint-kamailio.sh
├── transcriber_deepgram.py
├── requirements.txt
├── default.xml
├── config/
│   └── kamailio.cfg.template
├── recordings/
└── transcripts_deepgram/
Services
Kamailio

Kamailio handles:

SIP registration
SIP routing
Caller blocklist checks
Call rejection
FreeSWITCH routing
RTPengine integration
PostgreSQL access

Kamailio listens on:

UDP 5066
FreeSWITCH

FreeSWITCH handles:

SIP calls
Call processing
Audio recording
Media handling

FreeSWITCH uses:

UDP 5060
RTPengine

RTPengine handles RTP and SDP processing between SIP endpoints.

Kamailio connects to RTPengine using:

udp:127.0.0.1:2223
Deepgram Transcriber

The transcriber monitors:

/var/spool/freeswitch/recordings

It waits until a WAV file finishes writing, sends the audio to Deepgram, and saves the transcription as JSON.

Host recordings are stored in:

recordings/

Generated transcripts are stored in:

transcripts_deepgram/
Recording Format

Recordings use:

YYYY-MM-DD-HH-MM-SS_SOURCE_to_DESTINATION.wav

Example:

2026-08-18-20-03-55_1001_to_1002.wav

The filename contains:

Start time: 2026-08-18 20:03:55
Source: 1001
Destination: 1002
Transcription Format

Each WAV file generates a matching JSON file.

Example:

recordings/
└── 2026-08-18-20-03-55_1001_to_1002.wav


transcripts_deepgram/
└── 2026-08-18-20-03-55_1001_to_1002.json

Example JSON:

{
    "wav_file": "2026-08-18-20-03-55_1001_to_1002.wav",
    "processed_at": "2026-08-18 20:05:00",
    "processing_seconds": 2.5,
    "model": "deepgram-nova-3",
    "transcript": "Example transcript",
    "confidence": 0.98
}
Environment Variables

Create a .env file in the project root:

HOST_IP=YOUR_HOST_IP
DATABASE_URL=YOUR_DATABASE_URL
DEEPGRAM_API_KEY=YOUR_DEEPGRAM_API_KEY
DEEPGRAM_MODEL=nova-3
DEEPGRAM_LANGUAGE=ar
HOST_PROJECT_DIR=/path/to/kamailio-lab

Required variables:

HOST_IP
DATABASE_URL
DEEPGRAM_API_KEY

Optional variables:

DEEPGRAM_MODEL
DEEPGRAM_LANGUAGE
HOST_PROJECT_DIR
Build

Build all Docker images:

docker compose build

For a clean rebuild:

docker compose build --no-cache
Start

Start all services:

docker compose up -d

Check service status:

docker compose ps
Logs

Show all logs:

docker compose logs -f

Kamailio logs:

docker compose logs -f kamailio

FreeSWITCH logs:

docker compose logs -f freeswitch

Transcriber logs:

docker compose logs -f transcriber
Restart

Restart all services:

docker compose restart

Recreate containers after changing .env:

docker compose up -d --force-recreate

A full image rebuild is not required when only environment variables are changed.

Stop

Stop the services:

docker compose down

Stop and remove orphan containers:

docker compose down --remove-orphans
Kamailio Configuration

The main configuration template is:

config/kamailio.cfg.template

The following placeholders are replaced at container startup:

__HOST_IP__
__DATABASE_URL__

The generated configuration is:

/etc/kamailio/kamailio.cfg
FreeSWITCH Configuration

The FreeSWITCH image is built from:

Dockerfile.freeswitch

The startup script is:

docker-entrypoint-freeswitch.sh

The startup script applies HOST_IP when the container starts.

This allows the host IP to be changed without rebuilding the image.

Blocklist

Kamailio checks the caller against:

public.blocklist

A number is considered active in the blocklist when:

expires_at IS NULL

or:

expires_at > NOW()

Blocked calls receive:

403 Forbidden

Blocked calls are not forwarded to FreeSWITCH.

Blocked calls are stored in:

public.calls

with:

status = BLOCKED
Completed Calls

Completed calls are stored in:

public.calls

The application uses:

source
destination
started_at
ended_at
status
transcript
recording_path

Completed calls use:

status = COMPLETED
Database

The project uses PostgreSQL.

The database connection is provided through:

DATABASE_URL

Expected tables:

public.blocklist
public.calls
Current Recordings

Recordings are stored in:

recordings/

Each recording should have a corresponding transcript:

transcripts_deepgram/

Relationship:

recordings/<filename>.wav
        |
        v
transcripts_deepgram/<filename>.json
Useful Commands

List containers:

docker compose ps

Follow all logs:

docker compose logs -f

Check recordings:

ls -lah recordings/

Check transcripts:

ls -lah transcripts_deepgram/

Open FreeSWITCH CLI:

docker compose exec freeswitch fs_cli

Open Kamailio shell:

docker compose exec kamailio sh

Open transcriber shell:

docker compose exec transcriber sh
Security

Do not commit .env to Git.

Add this to .gitignore:

.env

Keep these values private:

DATABASE_URL
DEEPGRAM_API_KEY

Change any default credentials before using the system outside a development environment.

Architecture
                    SIP
                     |
                     v
              +-------------+
              |  Kamailio   |
              |    :5066    |
              +------+------+
                     |
             +-------+-------+
             |               |
             v               v
       RTPengine         FreeSWITCH
                            :5060
                              |
                              v
                         Recordings
                              |
                              v
                       Deepgram Worker
                              |
                              v
                         PostgreSQL
Main Files
Dockerfile.kamailio
Dockerfile.freeswitch
Dockerfile.transcriber_deepgram


docker-entrypoint-kamailio.sh
docker-entrypoint-freeswitch.sh


config/kamailio.cfg.template


transcriber_deepgram.py
docker-compose.yml
requirements.txt
default.xml
