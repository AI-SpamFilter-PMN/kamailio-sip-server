# Kamailio Lab

Docker-based VoIP lab utilizing Kamailio, FreeSWITCH, RTPengine, PostgreSQL, and Deepgram for real-time speech transcription and dynamic SIP call routing.

---

## Architecture

```text
                    SIP Traffic
                         |
                         v
                  +-------------+
                  |  Kamailio   |
                  |    :5066    |
                  +------+------+
                         |
             +-----------+-----------+
             |                       |
             v                       v
         RTPengine               FreeSWITCH
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

##Components
Kamailio (:5066): Acts as the main SIP proxy/registrar, enforcing blocklists, logging call attempts, and routing media via RTPengine to FreeSWITCH.

FreeSWITCH (:5060): Handles call logic, interactive media processing, and high-quality audio recordings.

RTPengine: Proxies RTP/SDP media streams between endpoints to ensure NAT traversal and low latency.

Deepgram Transcriber: An automated worker that monitors output recordings, sends audio to Deepgram, and yields transcribed text.

PostgreSQL: Central database holding blocklists, call logs (status, transcript, recording_path), and session metadata.

##Project Structure
Plaintext
kamailio-lab/
├── config/
│   └── kamailio.cfg.template         # Main Kamailio configuration template
├── recordings/                        # Generated WAV audio files
├── transcripts_deepgram/              # Output JSON transcripts
├── default.xml                        # FreeSWITCH core configuration
├── Dockerfile.freeswitch              # Build context for FreeSWITCH
├── Dockerfile.kamailio                # Build context for Kamailio
├── Dockerfile.transcriber_deepgram    # Build context for Transcriber worker
├── docker-compose.yml                 # Service orchestrator
├── docker-entrypoint-freeswitch.sh    # Entrypoint script for FreeSWITCH
├── docker-entrypoint-kamailio.sh      # Entrypoint script for Kamailio
├── requirements.txt                   # Python dependencies
└── transcriber_deepgram.py            # Automatic transcription script
##Environment Variables
Create a .env file in the project root directory before starting the stack:

Code snippet
HOST_IP=YOUR_HOST_IP
DATABASE_URL=postgresql://user:password@host:5432/dbname
DEEPGRAM_API_KEY=YOUR_DEEPGRAM_API_KEY
DEEPGRAM_MODEL=nova-3
DEEPGRAM_LANGUAGE=ar
HOST_PROJECT_DIR=/path/to/kamailio-lab
