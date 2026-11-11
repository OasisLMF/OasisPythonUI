"""Analysis status helpers shared by the standard UI and the Scenarios app."""
from datetime import datetime, timezone

IN_PROGRESS_STATUSES = ['INPUTS_GENERATION_QUEUED', 'INPUTS_GENERATION_STARTED',
                        'RUN_QUEUED', 'RUN_STARTED']

# A generate-and-run reports READY between input generation and the loss run,
# because OasisPlatform's record_input_files always sets READY (it ignores its
# analysis_finish_status argument). A READY analysis updated this recently is
# treated as still running.
READY_GRACE_SECONDS = 120


def is_active(analysis, now=None):
    """Whether an analysis is in progress, including the READY gap of a generate-and-run."""
    status = analysis.get('status')
    if status in IN_PROGRESS_STATUSES:
        return True
    if status == 'READY' and analysis.get('modified'):
        try:
            modified = datetime.fromisoformat(str(analysis['modified']).replace('Z', '+00:00'))
        except ValueError:
            return False
        now = now or datetime.now(timezone.utc)
        return (now - modified).total_seconds() < READY_GRACE_SECONDS
    return False
