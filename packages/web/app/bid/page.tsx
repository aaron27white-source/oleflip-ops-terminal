import { BidForm } from "@/components/bid/BidForm";
import { PageHeader } from "@/components/ui/primitives";

export default function BidPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="Bid Calculator"
        subtitle="Enter a machine and asking price to get an instant BUY/PASS call."
      />
      <BidForm />
    </div>
  );
}
