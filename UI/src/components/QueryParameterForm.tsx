import { Button, Stack, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import type { CypherQueryDefinition } from "../types/api";

function inferInitialValue(helpText: string): string {
  const exampleMatch = helpText.match(/Example:\s*([^;]+)/i);
  return exampleMatch ? exampleMatch[1].trim() : "";
}

function inferType(helpText: string, parameterName: string): "text" | "number" {
  if (parameterName.includes("hops") || /Example:\s*\d+/i.test(helpText)) {
    return "number";
  }
  return "text";
}

export function QueryParameterForm({
  query,
  isSubmitting,
  onSubmit
}: {
  query: CypherQueryDefinition;
  isSubmitting: boolean;
  onSubmit: (parameters: Record<string, string | number>) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});

  useEffect(() => {
    const nextValues: Record<string, string> = {};
    query.parameters.forEach((parameterName) => {
      nextValues[parameterName] = inferInitialValue(query.parameter_help[parameterName] ?? "");
    });
    setValues(nextValues);
  }, [query]);

  return (
    <Stack
      component="form"
      spacing={2.5}
      onSubmit={(event) => {
        event.preventDefault();
        const parameters = Object.fromEntries(
          query.parameters.map((parameterName) => {
            const helpText = query.parameter_help[parameterName] ?? "";
            const value = values[parameterName] ?? "";
            return [
              parameterName,
              inferType(helpText, parameterName) === "number" ? Number(value) : value
            ];
          })
        );
        onSubmit(parameters);
      }}
    >
      <Typography variant="subtitle1" fontWeight={700}>
        Parameters
      </Typography>
      {query.parameters.length === 0 ? (
        <Typography color="text.secondary">This endpoint does not require any parameters.</Typography>
      ) : (
        query.parameters.map((parameterName) => (
          <TextField
            key={parameterName}
            label={parameterName}
            type={inferType(query.parameter_help[parameterName] ?? "", parameterName)}
            helperText={query.parameter_help[parameterName] ?? "Required Cypher parameter."}
            value={values[parameterName] ?? ""}
            onChange={(event) =>
              setValues((currentValues) => ({
                ...currentValues,
                [parameterName]: event.target.value
              }))
            }
            fullWidth
            required
          />
        ))
      )}
      <Button type="submit" variant="contained" disabled={isSubmitting}>
        Run query
      </Button>
    </Stack>
  );
}
