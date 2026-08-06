import { createFileRoute } from "@tanstack/react-router";
import { UnderwriteConsole } from "@/components/underwrite-console";

const title = "Underwrite — Trust Runtime for DataHub";
const description =
  "Deterministic, fail-closed trust evaluation for DataHub metadata: column-level lineage, tag policy predicates, and staged metadata mutations.";


export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
    ],
  }),
  component: Index,
});

function Index() {
  return <UnderwriteConsole />;
}
