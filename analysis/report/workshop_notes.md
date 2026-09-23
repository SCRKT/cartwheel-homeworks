# Raindrop Workshop notes

## Scope and method

I inspected six fresh, read-only Cartwheel runs on September 22, 2026. The
runs covered all three roles and five tools: `get_order`, `search_products`,
`search_help_center`, `get_policy`, `get_my_store`, and `list_my_orders`.
Every run used `gpt-5.6-luna` and prompt version `f4cf9d1978a4`.

The Raindrop integration intentionally records the interaction boundary with
manual `begin` and `finish` events. It does not initialize a second
OpenTelemetry provider, because the existing Langfuse integration owns that
provider. Workshop therefore contains the input, final output, model,
conversation, role, scenario, and outcome for each run. I paired each
Workshop run with its Langfuse trace to inspect the existing model and tool
spans. This preserves the course's canonical Langfuse telemetry while making
the fresh runs visible in Workshop.

## Inspected runs

| Role | Case | Workshop run ID | Langfuse trace ID | Tools | Finding |
| --- | --- | --- | --- | --- | --- |
| Shopper | Order 301 status | `a56deead-2514-4813-8ef3-3d7e6dc43098` | `f16006a63f1c241130df7cbb25ed932e` | `get_order` | Accurate, concise status answer. |
| Shopper | Headphone comparison | `de7771c8-25f4-461f-a70d-00a9963c0069` | `c122055e1e542d9c890cf3d7ee7d1fa8` | `search_products` | Accurate comparison with product and store IDs. |
| Shopper | Delivered-order return policy | `04cd55eb-6a6f-4c42-83ec-44ba943028ac` | `6b57142d5b2b62b20f3d8aa0a70ab21c` | `search_help_center`, `get_policy` | Correctly cited `cw-returns` and `cw-escalations`; four tool calls were used to answer two policy questions. |
| Merchant | Store and five recent orders | `8dbf564a-6a29-46fd-bce4-31dd75e804cd` | `2e2dcab063052626d7a346456e0f0675` | `get_my_store`, `list_my_orders` | Accurate five-row summary; the tool returned 20 orders before the model selected five. |
| Merchant | Order 18 status | `23367e68-d7a7-43ee-be85-44022183ebfb` | `9bf71f7c799870f3c00549af99c201ee` | `get_order` | Accurate status and refund eligibility. |
| Support | Order 301 investigation | `f5e302e5-0aee-48d8-a6c0-ba7f24f93963` | `d49fd692998b130c632d64da163f45a9` | `get_order` | The order details were accurate, but the tool could not supply the requested owner. The answer also asserted that no records conflicted after reading one order record. |

## Suggested failures and unusual behavior

### 1. Support order lookup omits ownership data

The support user asked for the order owner. `get_order` returned order,
store, product, fulfillment, and refund fields, but no `user_id` or customer
identity. The assistant accurately said that the owner was not specified in
the record it received. This is primarily a tool-schema or support-workflow
gap rather than a model fabrication.

**Human decision: accepted as an isolated observation, not as a binary
failure mode.** Search the larger trace set for other support requests that
cannot be completed because authorized investigation fields are absent. If it
recurs, define a mode around incomplete authorized tool evidence.

### 2. Unsupported assurance that records do not conflict

The support answer ended with “I found no conflicting records,” but the trace
contains a single `get_order` call and one returned record. The evidence
supports “the returned order record is internally consistent”; it does not
show that multiple records or systems were compared.

**Human decision: revised into `retrieved_evidence_misstatement`.** Treat this
as an unsupported statement about the scope of retrieved evidence.
The positive boundary would require the answer to claim a broader check than
the tool activity actually performed. A close negative would say “the order
record contains no internal conflict.”

### 3. Order-list overfetching

The merchant requested five recent orders. `list_my_orders` returned 20, and
the model correctly displayed only five. The user-facing answer is correct,
but the tool performed more retrieval than the task required.

**Human decision: rejected as a response failure and retained as an
operational observation.** It may justify adding an optional `limit`
argument to `list_my_orders`, but it did not cause an incorrect or confusing
answer in this run.

## Uncertain or alternative explanations

The product comparison named the stores only as “Store 19.” One interpretation
is that this is incomplete product attribution because a shopper benefits from
a store name or product link. The alternative explanation is that the prompt
asked for stores and product IDs, and the only store field returned by
`search_products` was `store_id`; the response accurately presented all
available requested fields. The human reviewer retained this as an uncertain,
isolated tool-data hypothesis unless similar traces show that users cannot act
on search results.

The return-policy response told the shopper to ask for human review when no
policy applies but did not create an escalation or explicitly offer to create
one. Because the question was hypothetical and did not describe an actual
order needing intervention, creating a ticket would have been premature. The
human reviewer rejected this run as evidence of `missing_required_escalation`.

## Human decisions

1. **Revised** the unsupported “no conflicting records” assurance into
   `retrieved_evidence_misstatement`.
2. **Accepted as an isolated observation** the missing owner field in authorized
   support lookup; gather more examples before promoting it to a mode.
3. **Rejected as a response failure** the 20-row tool result because the final
   response correctly honored the five-row request.
4. **Retained as uncertain** store-name/link completeness in product search.
5. **Rejected as missing escalation** the hypothetical policy case.
