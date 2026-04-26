# Optional Exercise: Extend the Local Pipeline

Use this exercise after finishing the training, batch, and online inference lessons.

## Objective

Improve the local pipeline so you can compare a stronger model against the linear-regression baseline and inspect how that change affects both batch and online predictions.

## Suggested Workflow

1. Re-run the training notebook with one additional model choice.
2. Log both models to MLflow with clear run names and metrics.
3. Compare their validation results in a small summary table.
4. Update either the batch flow or the API configuration so it points to the better model version.
5. Run one batch scoring pass and one online prediction request with the updated model.

## Deliverables

- A short note describing the new model you tried.
- The validation metric comparison between baseline and updated model.
- One saved batch prediction file produced with the updated model.
- One sample online prediction response using the updated model.

## Hints

- The training notebook already builds features around `trip_route` and `trip_distance`.
- Good lightweight comparisons include a regularized linear model or a tree-based regressor.
- Keep the metric consistent so the comparison is easy to interpret.
- The active code resolves the prediction model from MLflow, so you can switch versions through the environment variables in `.env`.

## Stretch Goal

Add a second batch input dataset month and compare whether the newer model behaves similarly across both months.
