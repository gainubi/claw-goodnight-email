# claw-goodnight-email

A Codex/OpenClaw skill for running a small, human-feeling goodnight email project with ClawEmail or any mailbox-driven workflow.

It helps you:

- collect subscriptions by email
- enforce a fixed capacity cap
- handle unsubscribe requests
- collect story submissions with explicit anonymous-sharing consent
- compose nightly goodnight emails
- send the nightly batch through `mail-cli`

## What This Is

This project packages a lightweight operating model for a "write me every night" email product.

The default behavior is:

- subscribers email your project mailbox with their name and a clear opt-in
- the system stores subscribers in `data/state.json`
- each night it composes one email per active subscriber
- every email can optionally invite readers to reply with a story
- stories are only reusable if the sender explicitly says they can be shared anonymously

The tone is designed to feel warm, restrained, and human rather than like a newsletter or support bot.

## Repository Layout

```text
claw-goodnight-email/
├── README.md
├── SKILL.md
├── agents/openai.yaml
├── data/state.json
├── references/
├── scripts/goodnight_manager.py
├── scripts/send_nightly_batch.py
└── scripts/run_nightly_sender.sh
```

## Privacy And Sanitization

This open-source version is sanitized:

- no real subscriber emails
- no real names
- no real send logs
- no machine-specific absolute paths
- no private tokens or credentials

If you use this in production, keep runtime data and logs out of version control.

## Requirements

- Python 3.10+
- `mail-cli` available on `PATH` for real sending
- a mailbox profile already configured in `mail-cli`

The project can still be used for local testing without real sending by running `--dry-run`.

## Quick Start

From the project root:

```bash
python3 scripts/goodnight_manager.py --help
```

Subscribe one user manually:

```bash
python3 scripts/goodnight_manager.py subscribe \
  --email "reader@example.com" \
  --name "小雨"
```

Process an incoming email:

```bash
python3 scripts/goodnight_manager.py receive \
  --email "reader@example.com" \
  --subject "我想加入晚安邮件计划" \
  --body "你好，我叫小雨，我确认愿意接收每天一封晚安邮件。"
```

Preview tonight's batch without sending:

```bash
./scripts/run_nightly_sender.sh --dry-run
```

See a summary of current subscribers and stories:

```bash
python3 scripts/goodnight_manager.py summary
```

## Main Commands

`goodnight_manager.py`

- `receive`: classify and handle one incoming email
- `subscribe`: add a subscriber manually
- `unsubscribe`: remove a subscriber
- `compose-batch`: generate tonight's messages without sending
- `list-stories`: inspect collected stories and consent status
- `summary`: show active subscriber and story counts

`send_nightly_batch.py`

- sends the real nightly batch via `mail-cli`
- writes a JSONL send log
- updates `sent_count` and `last_sent_on` only after successful sends

`run_nightly_sender.sh`

- the recommended stable entry point for actual sending
- runs `send_nightly_batch.py` with a clean shell environment

## Runtime Files

Tracked sample file:

- `data/state.json`: empty starter state

Ignored runtime file:

- `data/send-log.jsonl`: append-only send log created at runtime

## How Story Sharing Works

The project never invents "reader stories."

Reusable story content must come from real replies and include explicit permission such as:

- "可以匿名分享"
- "你可以匿名整理后发出去"

Without that consent, the story can be stored for internal reading only and must not be shared in later emails.

## Recommended Publishing Notes

If you use this repo publicly, replace the placeholder mailbox with your own project address, for example:

```text
your-project@claw.163.com
```

You should also review:

- `SKILL.md` for behavior and tone
- `references/content-style.md` for voice
- `references/story-workflow.md` for consent rules

## License

MIT
