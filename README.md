# REST API → BigQuery demo

Mały przykład techniczny przepływu podobnego do integracji systemu hotelowego.

- REST API z tokenem Bearer
- retry/backoff dla błędów sieciowych
- normalizacja dostępności pokoi
- staging table + idempotentny MERGE do BigQuery
- kontener gotowy do Cloud Run / Cloud Run Job
- konfiguracja przez zmienne środowiskowe, bez sekretów w kodzie

Klucz rekordu dostępności: `hotel_id + room_type_id + date`, więc ponowne uruchomienie nie tworzy duplikatów.

## Zmienne środowiskowe

`HOTEL_API_URL`, `HOTEL_API_TOKEN`, `GCP_PROJECT`, `BQ_DATASET`, `HOTEL_ID`, `DATE_FROM`, `DATE_TO`.

To jest demonstrator architektury, nie kod klienta. Adapter do konkretnego API należy dopasować do Swaggera i rzeczywistych pól odpowiedzi.
