#  Zaphiro Technologies - API to manage a power grid model (Python)

To support the management of a simplified Single Line Diagram (SLD) of a power grid,
we need to implement a backend service that allows users to create, read, and aggregate
data about electrical components such as transformers, lines, and switches.

Managers should be able to add components, read data and generate reports.
Other users can only read components and reports.

## Data Model

## Measurement

A measurement represents a reading taken from a component at a specific time.

It has the following attributes:

- id
- timestamp
- value
- measurement_type (str, es. 'Voltage', 'Current', 'Power')

### Base Component

A component that represents a generic electrical component in the grid.

It has the following attributes:

- id
- name
- substation

Each component can have one or more measurements.

### Transformer

A transformer is a type of component that steps voltage up or down. It has the
same attributes as Component plus:

- capacity_mva
- voltage_kv

### Line

A line is a type of component that represents a power line connecting two
substations. It has the same attributes as Component plus:

- length_km
- voltage_kv

### Switch

A switch is a type of component that can open or close a circuit. It has the
same attributes as Component plus:

- status

## APIs

The service should expose the following RESTful API endpoints protected with JWT authentication:

- GET /components – list components (all users).
- POST /components – add a new component (manager only).
- PUT /components/{id} – update a component (manager only).
- DELETE /components/{id} – delete a component (manager only).
- POST /measurements – add a measurement to a component (manager only).
- POST /reports – generate a report asynchronously for a given period (manager only).
- GET /reports – list available reports (all users).
- GET /reports/{id} – get a specific report (all users).

### Reports

Reports should be generated asynchronously (you have to imagine they can be
based on a very large amount of information and take long time to be generated)
and include the following information:

- Total number of components by type
- Total capacity of transformer per voltage level
- Total length of lines per voltage level
- Average measurement values per measurement type and component type using daily
 buckets.

### Authentication

The service should implement JWT-based authentication with two roles:

- manager: can access all endpoints
- user: can only access GET endpoints

## Validation

Test the API using at least 100 components and 10000 measurements (per component)
and generating report over different periods.

## Deliverables

Please provide a link to a GitHub repository containing:

1. The Application source code and Dockerfile.
2. Documentation (README).
