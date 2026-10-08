"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Users, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function CustomersPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    api.getCustomers()
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError("Unable to load customer analytics.");
        setLoading(false);
      });
  }, []);

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0);

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

  const customers = data?.customers || [];

  if (customers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <Card className="max-w-md w-full border-dashed">
          <CardContent className="flex flex-col items-center p-12 text-center">
            <Users className="h-12 w-12 text-gray-300 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900">No customers found.</h2>
            <p className="text-sm text-gray-500 mt-2">
              Import orders containing customer IDs to see customer analytics.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customer Intelligence</h1>
          <p className="text-gray-500">
            Analyze customer segments and lifetime value across {data.summary.total_customers} active customers.
          </p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Customers</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.summary.total_customers}</h3>
            </div>
            <div className="h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center">
              <Users className="h-6 w-6 text-indigo-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">New Customers</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.summary.new_customers}</h3>
            </div>
            <div className="h-12 w-12 rounded-full bg-blue-50 flex items-center justify-center">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Repeat Customers</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.summary.repeat_customers}</h3>
            </div>
            <div className="h-12 w-12 rounded-full bg-purple-50 flex items-center justify-center">
              <Users className="h-6 w-6 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4">Customer ID</th>
                <th className="px-6 py-4">Segment</th>
                <th className="px-6 py-4 text-right">Orders</th>
                <th className="px-6 py-4 text-right">Lifetime Revenue</th>
                <th className="px-6 py-4 text-right">Avg Order Value</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c: any) => (
                <tr key={c.customer_id} className="border-b hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-gray-900">{c.external_id}</div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant="secondary" className={
                      c.segment === 'RETURNING' ? 'bg-purple-100 text-purple-800' :
                      c.segment === 'NEW' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }>
                      {c.segment}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 text-right font-medium">
                    {c.order_count}
                  </td>
                  <td className="px-6 py-4 text-right font-bold text-gray-900">
                    {formatCurrency(c.total_revenue)}
                  </td>
                  <td className="px-6 py-4 text-right text-gray-600">
                    {formatCurrency(c.average_order_value)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
