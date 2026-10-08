"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function ReportsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [days, setDays] = useState<number>(30);

  useEffect(() => {
    setLoading(true);
    api.getOverview(days)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError("Unable to load reports.");
        setLoading(false);
      });
  }, [days]);

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0);
    
  const formatDecimal = (val: number) => (val || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

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
  
  const s = data?.summary;
  
  if (!s || s.spend === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)]">
        <Card className="max-w-md w-full border-dashed">
          <CardContent className="flex flex-col items-center p-12 text-center">
            <FileText className="h-12 w-12 text-indigo-200 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900">Reports Unavailable</h2>
            <p className="text-sm text-gray-500 mt-2 mb-6">
              Reports will generate once sufficient business data is available.
            </p>
            <Link href="/settings">
              <Button className="bg-indigo-600 hover:bg-indigo-700">Import Data</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Consolidated Business Report</h1>
          <p className="text-gray-500">
            A comprehensive summary of your tracked business metrics.
          </p>
        </div>
        <div className="flex space-x-2 bg-white rounded-lg border p-1 shadow-sm">
          <Button 
            variant={days === 7 ? "default" : "ghost"} size="sm" 
            onClick={() => setDays(7)} className={days === 7 ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 shadow-none" : "text-gray-600"}
          >
            7 Days
          </Button>
          <Button 
            variant={days === 30 ? "default" : "ghost"} size="sm" 
            onClick={() => setDays(30)} className={days === 30 ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 shadow-none" : "text-gray-600"}
          >
            30 Days
          </Button>
          <Button 
            variant={days === 90 ? "default" : "ghost"} size="sm" 
            onClick={() => setDays(90)} className={days === 90 ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 shadow-none" : "text-gray-600"}
          >
            90 Days
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        <Card>
          <CardHeader className="bg-gray-50 border-b">
            <CardTitle className="text-lg">Financial Performance</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Tracked Revenue</span>
                <span className="font-semibold">{formatCurrency(s.revenue)}</span>
              </div>
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Attributed Revenue</span>
                <span className="font-semibold">{s.order_revenue > 0 ? formatCurrency(s.order_revenue) : 'Unavailable'}</span>
              </div>
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Marketing Spend</span>
                <span className="font-semibold text-red-600">-{formatCurrency(s.spend)}</span>
              </div>
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Product Cost</span>
                <span className="font-semibold text-red-600">
                  {s.product_cost > 0 ? `-${formatCurrency(s.product_cost)}` : 'Unavailable'}
                </span>
              </div>
              <div className="flex justify-between p-4 bg-indigo-50/30">
                <span className="font-bold text-gray-900">Gross Profit (Tracked)</span>
                <span className={`font-bold ${s.profit >= 0 ? 'text-indigo-600' : 'text-red-600'}`}>
                  {formatCurrency(s.profit)}
                </span>
              </div>
              <div className="flex justify-between p-4 bg-green-50/50">
                <span className="font-bold text-gray-900" title="Revenue minus marketing spend and product cost">Contribution Profit</span>
                <span className={`font-bold ${s.contribution_profit !== null ? (s.contribution_profit >= 0 ? 'text-green-700' : 'text-red-700') : 'text-gray-500'}`}>
                  {s.contribution_profit !== null ? formatCurrency(s.contribution_profit) : 'Unavailable'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="bg-gray-50 border-b">
            <CardTitle className="text-lg">Key Metrics & KPIs</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              <div className="flex justify-between p-4">
                <span className="text-gray-600">ROAS (Return on Ad Spend)</span>
                <span className="font-semibold">{formatDecimal(s.roas)}x</span>
              </div>
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Profit ROAS</span>
                <span className="font-semibold">{s.contribution_profit !== null ? formatDecimal(s.profit_roas) + 'x' : 'Unavailable'}</span>
              </div>
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Contribution Margin</span>
                <span className="font-semibold">{s.contribution_margin !== null ? `${formatDecimal(s.contribution_margin)}%` : 'Unavailable'}</span>
              </div>
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Total Orders</span>
                <span className="font-semibold">{s.total_orders || 0}</span>
              </div>
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Total Customers</span>
                <span className="font-semibold">{s.total_customers || 0}</span>
              </div>
              <div className="flex justify-between p-4">
                <span className="text-gray-600">Total Tracked Conversions</span>
                <span className="font-semibold">{s.conversions || 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
