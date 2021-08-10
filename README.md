# cross_modality_query

Server-side code for HuBMAP Cells API.
[Python](https://github.com/hubmapconsortium/hubmap-api-py-client) client available.


## Development Process

### To release via TEST infrastructure

-    Make new feature or bug fix branches from test-release.
-    Make PRs to test-release. (This is the default branch.)
-    As a codeowner, Sean is automatically assigned as a reviewer to each PR. When all other reviewers have approved, he will approve as well, merge to TEST infrastructure, and redeploy and reindex the TEST instance.
-    Developer or someone on the team who is familiar with the change will test/qa the change
-    When any current changes in the test-release have been approved after test/qa on TEST, Sean will release to PROD.

### To work on features in the development environment before ready for testing and releasing

-    Make new feature branches from test-release.
-    Make PRs to dev-integrate.
-    As a codeowner, Sean is automatically assigned as a reviewer to each PR. When all other reviewers have approved, he will approve as well, merge to devel, and redeploy and reindex the DEV instance.
-    When a feature branch is ready for testing and release, make a PR to test-release for deployment and testing on the TEST infrastructure as above.

## Usage

This is only a high-level outline of the API:
See the [Python client examples](https://github.com/hubmapconsortium/hubmap-api-py-client/tree/main/examples) for details.

The API supports a small number of basic operations which can be combined to construct more complex queries.
The API runs at a **`base_url`**: Currently `https://cells.api.hubmapconsortium.org/api` is available.

Issuing a `POST` to `{base_url}/{output_type}/`, with query parameters in the body,
will return a **query handle** representing `output_type` entities.
`output_type` is currently limited to `cell`, `organ`, `gene`, `dataset`, `protein` , and `cluster`.
(The Python and Javascript interfaces provide a **query** abstraction, so you don't need to deal directly with the handle.)

Issuing a `POST` to `{base_url}/{output_type}/` with no query parameters will retury a **query handle** representing all entities of `output_type`

Issuing a `POST` to `{base_url}/{operation}/` (where `operation` is `union`, `intersection`, or `difference`),
with query handles provided as `key_one` and `key_two` in the body, will return a new query handle,
representing the result of the operation.

Issuing a `POST` to `{base_url}/{statistic}/` (where `statistic` is `mean`, `stddev`, `min`, or `max`)
with a query handle as `key_one` and a gene or protein identifier as `var_id` will return
a statistical report on the expression of that gene/protein in the set provided.

Three endpoints are provided for getting more information, given a query handle:
- `{base_url}/count/` will return the number of matching entities.
- `{base_url}/{set_type}evaluation/` will return a pre-defined set of fields from the entities selected by the query in an arbitrary order.
- `{base_url}/{set_type}detailevaluation/` will return both pre-defined and user-defined fields, optionally sorted by a specified field.

The `detailevaluation` endpoints may be slower that `evaluation`. 
To page through the results, `offset` and `limit` can be provided to both `evaluation` and `detailevaluation`.

## Coverage

At this point, only some of the possible combinations of constraint type and output type have been implemented.
This matrix will be expanded over time, but queries that are better satisfied by other APIs will not be duplicated by this API.

| output / constraint | `none`    | `cell`    | `cluster` | `dataset` | `gene`    | `organ`   | `protein` | `modality` |
| ------------------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- |
| `cells`             | ✓         | ✓         | ✓         | ✓         | ✓         | ✓         | ✓         | ✓         |
| `clusters`          | ✓         | ✓         | ✓         | ✓         | ✓         |           |           |           |
| `datasets`          | ✓         | ✓         | ✓         | ✓         |           |           |           | ✓         |
| `genes`             | ✓         |           | ✓         |           | ✓         | ✓         |           |           |
| `organs`            | ✓         |           |           |           | ✓         | ✓         |           |           |
| `proteins`          | ✓         |           | ✓         |           |           | ✓         |           |           |
