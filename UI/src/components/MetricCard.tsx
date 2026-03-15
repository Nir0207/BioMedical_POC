import { Paper, Stack, Typography } from "@mui/material";

export function MetricCard({
  eyebrow,
  value,
  detail,
  testId
}: {
  eyebrow: string;
  value: string;
  detail: string;
  testId: string;
}) {
  return (
    <Paper className="rounded-[28px] border border-white/70 bg-white/90 p-6 shadow-dashboard" data-testid={testId}>
      <Stack spacing={1}>
        <Typography variant="overline" className="tracking-[0.24em] text-sea">
          {eyebrow}
        </Typography>
        <Typography variant="h4" data-testid={`${testId}-value`}>
          {value}
        </Typography>
        <Typography color="text.secondary">{detail}</Typography>
      </Stack>
    </Paper>
  );
}
