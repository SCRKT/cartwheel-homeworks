# Review interface comparison

## Observation basis

I inspected eight representative Cartwheel sessions in Langfuse, including
single-turn order lookup, refund, cancellation, authorization denial, damaged
order escalation, ambiguous order search, and multi-turn dispute cases. The
standard view preserves detailed model and tool observations, but Cartwheel
creates one Langfuse trace per user turn. A follow-up therefore appears apart
from the earlier tool evidence unless the reviewer manually follows the shared
session identifier. Repeated system prompts and tool schemas also occupy much
of the observation list, while the scenario's expected behavior is not beside
the answer being judged.

## Design retained

I retained distinct visual roles and a single chronological event stream. User
messages are blue, assistant messages are green, and each tool call and result
share an amber card. This keeps provenance visible while making the causal
sequence easier to scan. Direct links back to the canonical Langfuse trace are
shown below every turn.

## Design changed

The review unit is a conversation session rather than an isolated trace. The
server groups records by `cartwheel.session_id`, sorts the turns and their
observations by timestamp, and shows the complete conversation in the center
column. The scenario criterion and reference sit in a fixed review panel beside
the timeline. A reviewer can attach free-form evidence to selected trace
content, record the first failure or “no failure observed” for a specific turn,
and later apply each accepted binary mode to every trace. AI suggestions have a
separate visual treatment and require explicit acceptance or rejection.

## Remaining limitation

The conversation display reads the committed Homework 3 export, so newly
created Langfuse traces do not appear until the export is refreshed. Accepted
binary labels sync back to Langfuse when it is available, but open-code notes
remain in the local analysis state. The interface also displays only activity
present in the exported observations; it cannot reconstruct hidden model state
that was never traced.

