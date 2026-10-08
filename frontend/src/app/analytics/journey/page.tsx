"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Route, Package, Calendar } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function JourneyPage() {
  const [journey, setJourney] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadJourney() {
      try {
        const data = await api.getJourney();
        setJourney(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadJourney();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-gray-500 animate-pulse">Loading journey data...</div>;
  }

  if (journey.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)]">
        <Card className="max-w-md w-full border-dashed">
          <CardContent className="flex flex-col items-center p-12 text-center">
            <Route className="h-12 w-12 text-indigo-200 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900">Journey Analysis</h2>
            <p className="text-sm text-gray-500 mt-2">
              Customer journey data will appear after customer and order data is connected.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Customer Journey Timeline</h1>
        <p className="text-gray-500">Real verified order history across your customer base.</p>
      </div>

      <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
        {journey.map((event, i) => (
          <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-indigo-100 text-indigo-600 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
              <Package className="h-4 w-4" />
            </div>
            
            <Card className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] p-4 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-2">
                <div className="text-sm font-semibold text-indigo-600">Customer: {event.customer_id}</div>
                <Badge variant={event.order_status === 'completed' ? 'default' : 'secondary'} className="capitalize bg-green-100 text-green-700 hover:bg-green-100">
                  {event.order_status}
                </Badge>
              </div>
              <div className="flex items-center text-xs text-gray-500 mb-4">
                <Calendar className="h-3 w-3 mr-1" />
                {new Date(event.order_date).toLocaleDateString()} at {new Date(event.order_date).toLocaleTimeString()}
              </div>
              
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-900">Order: {event.order_id}</div>
                <div className="text-lg font-bold text-gray-900">₹{(event.order_value || 0).toLocaleString()}</div>
                
                {event.products && event.products.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Products Purchased</div>
                    <ul className="text-sm text-gray-700 list-disc list-inside">
                      {event.products.map((p: string, idx: number) => (
                        <li key={idx} className="truncate">{p}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>
          </div>
        ))}
      </div>
    </div>
  );
}
