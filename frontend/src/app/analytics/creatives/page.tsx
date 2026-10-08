"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Image as ImageIcon, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function CreativesPage() {
  const [creatives, setCreatives] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getCreatives()
      .then(data => {
        setCreatives(data);
        setLoading(false);
      })
      .catch(err => {
        setError("Unable to load creatives. Please try again.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="animate-pulse h-96 bg-gray-200 rounded-xl m-6"></div>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-red-500">
        <AlertCircle className="h-10 w-10 mb-2" />
        <p>{error}</p>
      </div>
    );
  }

  if (creatives.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)]">
        <Card className="max-w-md w-full border-dashed">
          <CardContent className="flex flex-col items-center p-12 text-center">
            <ImageIcon className="h-12 w-12 text-gray-300 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900">No creatives have been added yet.</h2>
            <p className="text-sm text-gray-500 mt-2">
              Import creative metadata or connect ad accounts to see creative performance.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Creatives</h1>
        <p className="text-gray-500">Analyze performance across all your ad creatives.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {creatives.map((creative) => (
          <Card key={creative.id} className="overflow-hidden">
            <div className="h-48 bg-gray-100 flex items-center justify-center border-b">
              <ImageIcon className="h-10 w-10 text-gray-300" />
            </div>
            <CardContent className="p-4">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-gray-900 truncate">{creative.name}</h3>
                <Badge variant="outline" className="bg-gray-50">{creative.platform}</Badge>
              </div>
              <p className="text-sm text-gray-500 italic mt-4">Performance data unavailable.</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
