# cross_modality_query

Server-side code for HuBMAP Cells API.
[Python](https://github.com/hubmapconsortium/hubmap-api-py-client) and 
[Javascript](https://github.com/hubmapconsortium/hubmap-api-js-client) clients available.

## Usage

This is only a high-level outline of the API:
See the [Python client examples](https://github.com/hubmapconsortium/hubmap-api-py-client/tree/main/examples) for details.

The API supports a small number of basic operations which can be combined to construct more complex queries.
The API runs at a **`base_url`**: Currently `https://cells.dev.hubmapconsortium.org/api` is available.

Issuing a `POST` to `{base_url}/{output_type}/`, with query parameters in the body,
will return a **query handle** representing `output_type` entities.
`output_type` is currently limited to `cell`, `organ`, `gene`, and `cluster`.
(The Python and Javascript interfaces provide a **query** abstraction, so you don't need to deal directly with the handle.)

Issuing a `POST` to `{base_url}/{operation}/` (where `operation` is `union`, `intersection`, or `difference`),
with query handles provided as `key_one` and `key_two` in the body, will return a new query handle,
representing the result of the operation.

Three endpoints are provided for getting more information, given a query handle:
- `{base_url}/count/` will return the number of matching entities.
- `{base_url}/evaluation/` will return a pre-defined set of fields from the entities selected by the query in an arbitrary order.
- `{base_url}/detailevaluation/` will return both pre-defined and user-defined fields, optionally sorted by a specified field.

The `detailevaluation` endpoint may be slower that `evaluation`. 
To page through the results, `offset` and `limit` can be provided to both `evaluation` and `detailevaluation`.

## Coverage

At this point, only some of the possible combinations of constraint type and output type have been implemented.
This matrix will be expanded over time, but queries that are better satisfied by other APIs will not be duplicated by this API.

| output / constraint | `cell`    | `cluster` | `dataset` | `gene`    | `organ`   | `protein` |
| ------------------- | --------- | --------- | --------- | --------- | --------- | --------- |
| `cells`             |           |           | ✓         | ✓         | ✓         | ✓         |
| `clusters`          |           |           |           | ✓         |           |           |
| `genes`             |           | ✓         |           |           | ✓         |           |
| `organs`            | ✓         |           |           | ✓         |           |           |
