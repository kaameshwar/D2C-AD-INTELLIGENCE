"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  Legend
} from 'recharts';
import { Target, AlertTriangle, Lightbulb, ArrowRight, TrendingUp, DollarSign, Activity, Users, Percent, Package, UserCheck } from "lucide-react";
import Link from "next/link";

export default function CommandCenter() {
  const [overview, setOverview] = useState<any>(null);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState<number>(7);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [overviewData, oppData, campData] = await Promise.all([
          api.getOverview(days),
          api.getOpportunities(),
          api.getCampaigns()
        ]);
        setOverview(overviewData);
        setOpportunities(oppData);
        setCampaigns(campData);
      } catch (e) {
        console.error(e);
        setError("Failed to load dashboard data. Please try again later.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [days]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <AlertTriangle className="h-12 w-12 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">Oops, something went wrong</h2>
        <p className="text-gray-500 mt-2">{error}</p>
        <Button onClick={() => window.location.reload()} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
          Retry
        </Button>
      </div>
    );
  }

  if (loading && !overview) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="flex justify-between items-center">
          <div className="h-10 w-96 bg-gray-200 rounded"></div>
          <div className="h-10 w-32 bg-gray-200 rounded"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-xl"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="col-span-2 h-96 bg-gray-200 rounded-xl"></div>
          <div className="h-96 bg-gray-200 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (campaigns.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-12rem)] max-w-lg mx-auto text-center">
        <div className="h-20 w-20 bg-indigo-100 rounded-full flex items-center justify-center mb-6">
          <Target className="h-10 w-10 text-indigo-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to DeciFlow</h2>
        <p className="text-gray-500 mb-8">
          Your workspace is ready, but you have no campaign data yet. Upload your first campaign dataset to start analyzing performance and uncovering AI opportunities.
        </p>
        <Link href="/settings">
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-lg px-8 py-6 rounded-full">
            Connect Data
          </Button>
        </Link>
      </div>
    );
  }

  const formatCurrency = (val: number) => `₹${(val || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  const formatDecimal = (val: number) => (val || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  
  const summary = overview?.summary || {};
  const chartData = overview?.timeseries || [];
  const topOpp = opportunities[0];

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            Performance Overview
          </h1>
          <p className="text-gray-500 mt-2 text-lg">
            Monitor your real-time campaign metrics.
          </p>
        </div>
        
        <div className="flex space-x-2 bg-white rounded-lg border p-1 shadow-sm">
          <Button 
            variant={days === 7 ? "default" : "ghost"} 
            size="sm" 
            onClick={() => setDays(7)}
            className={days === 7 ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 shadow-none" : "text-gray-600"}
          >
            Last 7 Days
          </Button>
          <Button 
            variant={days === 30 ? "default" : "ghost"} 
            size="sm" 
            onClick={() => setDays(30)}
            className={days === 30 ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 shadow-none" : "text-gray-600"}
          >
            Last 30 Days
          </Button>
          <Button 
            variant={days === 90 ? "default" : "ghost"} 
            size="sm" 
            onClick={() => setDays(90)}
            className={days === 90 ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 shadow-none" : "text-gray-600"}
          >
            Last 90 Days
          </Button>
        </div>
      </div>

      {/* Database-Driven KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4">
        
        <Card className="col-span-1 xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-medium text-gray-500 uppercase" title="Total revenue tracked by marketing platforms.">Tracked Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(summary.revenue)}</div>
            {summary.data_completeness?.orders_exist && (
              <p className="text-xs text-gray-500 mt-1" title="Revenue strictly attributed from actual database orders.">Attributed Revenue: {formatCurrency(summary.order_revenue)}</p>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-1 xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-medium text-gray-500 uppercase" title="Total spend across all marketing channels.">Marketing Spend</CardTitle>
            <Activity className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(summary.spend)}</div>
          </CardContent>
        </Card>

        <Card className={`col-span-1 xl:col-span-2 ${summary.contribution_profit !== null ? 'border-green-100 bg-green-50/30' : 'border-indigo-100 bg-indigo-50/30'}`}>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className={`text-xs font-medium uppercase ${summary.contribution_profit !== null ? 'text-green-700' : 'text-indigo-700'}`} title={summary.contribution_profit !== null ? "Revenue minus product cost and marketing spend." : "Revenue minus marketing spend."}>
              {summary.contribution_profit !== null ? 'Contribution Profit' : 'Gross Profit'}
            </CardTitle>
            <TrendingUp className={`h-4 w-4 ${summary.contribution_profit !== null ? 'text-green-500' : 'text-indigo-500'}`} />
          </CardHeader>
          <CardContent>
            {summary.contribution_profit !== null ? (
              <>
                <div className={`text-2xl font-bold ${summary.contribution_profit >= 0 ? 'text-green-700' : 'text-red-600'}`}>
                  {formatCurrency(summary.contribution_profit)}
                </div>
                <p className="text-xs text-gray-500 mt-1">Margin: {summary.contribution_margin?.toFixed(2)}%</p>
              </>
            ) : (
              <>
                <div className={`text-2xl font-bold ${summary.profit >= 0 ? 'text-indigo-700' : 'text-red-600'}`}>
                  {formatCurrency(summary.profit)}
                </div>
                <p className="text-xs text-gray-500 mt-1" title="Product cost data required for true contribution profit.">
                  Contribution Profit unavailable
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-1 xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-medium text-gray-500 uppercase" title="Revenue generated per unit of marketing spend.">ROAS</CardTitle>
            <Percent className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{formatDecimal(summary.roas)}x</div>
            <p className="text-xs text-gray-500 mt-1" title="Contribution profit generated per unit of marketing spend.">Profit ROAS: {summary.contribution_profit !== null ? formatDecimal(summary.profit_roas) : "Unavailable"}</p>
          </CardContent>
        </Card>

        {summary.total_orders > 0 && (
          <Card className="col-span-1 xl:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-medium text-gray-500 uppercase">Total Orders</CardTitle>
              <Package className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{(summary.total_orders || 0).toLocaleString()}</div>
            </CardContent>
          </Card>
        )}

        {summary.total_customers > 0 && (
          <Card className="col-span-1 xl:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-medium text-gray-500 uppercase">Customers</CardTitle>
              <UserCheck className="h-4 w-4 text-indigo-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{(summary.total_customers || 0).toLocaleString()}</div>
            </CardContent>
          </Card>
        )}

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Performance Trend</CardTitle>
            <CardDescription>Revenue vs Spend vs Profit (Last {days} Days)</CardDescription>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: '#6b7280', fontSize: 12 }} 
                      dy={10}
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: '#6b7280', fontSize: 12 }}
                      tickFormatter={(value) => `₹${value >= 1000 ? (value/1000) + 'k' : value}`} 
                    />
                    <Tooltip 
                      formatter={(value: any) => `₹${Number(value).toLocaleString()}`}
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px' }} />
                    <Line type="monotone" dataKey="revenue" name="Revenue" stroke="#4f46e5" strokeWidth={3} dot={chartData.length < 14} activeDot={{ r: 6 }} />
                    <Line type="monotone" dataKey="spend" name="Spend" stroke="#ef4444" strokeWidth={3} dot={chartData.length < 14} />
                    <Line type="monotone" dataKey="profit" name="Profit" stroke="#10b981" strokeWidth={3} dot={chartData.length < 14} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[350px] flex items-center justify-center text-gray-400 border-2 border-dashed rounded-lg">
                No time-series data available for this range
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Opportunity */}
        {topOpp ? (
          <Card className="bg-gradient-to-br from-indigo-900 to-slate-900 text-white border-none shadow-xl flex flex-col h-full">
            <CardHeader>
              <div className="flex justify-between items-start">
                <Badge variant="secondary" className="bg-indigo-500/20 text-indigo-200 hover:bg-indigo-500/30 border-none">
                  AI RECOMMENDATION
                </Badge>
                <div className="text-right">
                  <div className="text-3xl font-bold text-green-400">+{formatCurrency(topOpp?.projected_profit)}</div>
                  <div className="text-xs text-indigo-300">Projected Profit</div>
                </div>
              </div>
              <CardTitle className="text-xl mt-4 leading-tight">{topOpp?.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 flex-1 flex flex-col">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-indigo-200">Opportunity Score</span>
                  <span className="font-semibold text-white">{topOpp?.score} / 100</span>
                </div>
                <div className="w-full bg-indigo-950 rounded-full h-2">
                  <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${topOpp?.score}%` }}></div>
                </div>
              </div>
              
              <div className="bg-indigo-950/50 rounded-lg p-4 space-y-2 flex-1">
                <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">Evidence</h4>
                <ul className="space-y-1">
                  {topOpp?.evidence?.map((ev: string, i: number) => (
                    <li key={i} className="text-sm flex items-center text-indigo-100">
                      <div className="h-1.5 w-1.5 rounded-full bg-green-400 mr-2 flex-shrink-0"></div>
                      <span className="leading-snug">{ev}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex flex-col gap-2 pt-2">
                <Link href={`/optimization/simulator?recommendation_id=${topOpp.id}`}>
                  <Button className="w-full bg-indigo-500 hover:bg-indigo-600 text-white border-none">
                    Simulate Action <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-gray-50 border-dashed flex flex-col justify-center items-center text-center p-8 h-full">
            <Lightbulb className="h-12 w-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No opportunities detected</h3>
            <p className="text-sm text-gray-500 mt-2">DeciFlow requires more data to generate reliable recommendations.</p>
          </Card>
        )}
      </div>

    </div>
  );
}
