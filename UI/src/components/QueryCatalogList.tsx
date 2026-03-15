import { Chip, List, ListItemButton, ListItemText, Stack, Typography } from "@mui/material";
import type { CypherQueryDefinition } from "../types/api";

export function QueryCatalogList({
  queries,
  selectedQueryId,
  onSelect
}: {
  queries: CypherQueryDefinition[];
  selectedQueryId: string | null;
  onSelect: (query: CypherQueryDefinition) => void;
}) {
  return (
    <List disablePadding className="space-y-3">
      {queries.map((query) => (
        <ListItemButton
          key={query.query_id}
          selected={selectedQueryId === query.query_id}
          className="rounded-3xl border border-white/70 bg-white/85 px-4 py-3"
          onClick={() => onSelect(query)}
          data-testid={`query-item-${query.query_id.replaceAll("/", "-")}`}
          aria-label={query.query_id}
        >
          <Stack direction="row" spacing={2} alignItems="start" width="100%">
            <ListItemText
              primary={<Typography fontWeight={700}>{query.name.replaceAll("_", " ")}</Typography>}
              secondaryTypographyProps={{ component: "div" }}
              secondary={
                <Stack spacing={1} mt={1}>
                  <Typography variant="body2" color="text.secondary" component="div">
                    {query.description}
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    <Chip label={query.category} size="small" />
                    {query.parameters.length > 0 ? (
                      <Chip label={`${query.parameters.length} params`} size="small" color="secondary" />
                    ) : (
                      <Chip label="No params" size="small" color="success" />
                    )}
                  </Stack>
                </Stack>
              }
            />
          </Stack>
        </ListItemButton>
      ))}
    </List>
  );
}
