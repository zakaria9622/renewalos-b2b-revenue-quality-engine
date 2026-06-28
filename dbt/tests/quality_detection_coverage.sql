select *
from {{ ref('dq_incident_detection_coverage') }}
where detection_status <> 'detected'
