import { Card, CardContent } from "@/components/ui/card";
import { Hammer } from "lucide-react";

export default function PlaceholderPage() {
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)]">
      <Card className="max-w-md w-full border-dashed">
        <CardContent className="flex flex-col items-center p-12 text-center">
          <Hammer className="h-12 w-12 text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Module Under Construction</h2>
          <p className="text-sm text-gray-500 mt-2">
            This feature requires additional backend API integration. The UI structure is prepared for future development.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
