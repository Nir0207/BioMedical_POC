import { Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";

export function ResultsTable({ records }: { records: Array<Record<string, unknown>> }) {
  if (records.length === 0) {
    return (
      <Paper className="rounded-[28px] border border-dashed border-sand bg-white/60 p-6">
        <Typography color="text.secondary">No records returned.</Typography>
      </Paper>
    );
  }

  const columns = Array.from(new Set(records.flatMap((record) => Object.keys(record))));

  return (
    <Paper className="overflow-hidden rounded-[28px] border border-white/70 bg-white/90">
      <Table size="small">
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell key={column}>{column}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {records.map((record, index) => (
            <TableRow key={`${index}-${Object.keys(record).join("-")}`}>
              {columns.map((column) => (
                <TableCell key={`${index}-${column}`}>
                  <pre className="m-0 whitespace-pre-wrap text-xs">
                    {JSON.stringify(record[column] ?? null, null, 2)}
                  </pre>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
}
