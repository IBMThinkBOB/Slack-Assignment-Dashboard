# Excel File Format

The platform accepts `.xlsx` files for bulk project import.

---

## Required Columns

| Column Name | Type | Description |
|---|---|---|
| `Project Name` | Text | Name of the project (**required**) |
| `Customer` | Text | Customer or client name (**required**) |
| `Description` | Text | Project description |
| `Start Date` | Date | Project start date (e.g. `2024-06-01`) |
| `End Date` | Date | Project end date |
| `Project Type` | Text | `Paid`, `Presales`, `Internal`, `Support` |
| `Priority` | Text | `High`, `Medium`, `Low` |
| `Progress` | Number | Progress percentage `0`–`100` |
| `Manager` | Text | Project manager name |
| `Practice` | Text | Practice or team name |
| `Required Skills` | Text | Comma-separated list, e.g. `Storage Scale, Linux, AWS` |

---

## Notes

- The first row must be the header row with exactly these column names (case-sensitive).
- `Project Name` and `Customer` are used as the upsert key — uploading the same project twice updates the existing record.
- Extra columns are ignored.
- Missing optional columns are accepted; missing **required** columns return a `422` error listing what is absent.
- Dates should be Excel date cells or ISO strings (`YYYY-MM-DD`).

---

## Sample File

See [`sample-data/sample-projects.xlsx`](../sample-data/sample-projects.xlsx) for a working example with 5 projects.

---

## Upload API

```bash
curl -X POST http://localhost:8000/excel/upload \
  -H "X-Role: admin" \
  -F "file=@sample-data/sample-projects.xlsx"
```

Response:

```json
{
  "inserted": 3,
  "updated": 2,
  "total": 5
}
```
