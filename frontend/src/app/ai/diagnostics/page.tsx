"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, AlertTriangle, TrendingUp, DollarSign, Target, CheckCircle2 } from "lucide-react";

export default function DiagnosticsPage() {
  const [diag, setDiag] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDiagnostics().then(data => {
      setDiag(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="animate-pulse h-96 bg-gray-200 rounded-xl m-6"></div>;

  const formatCurrency = (val: number) => `₹${(val || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  const formatDecimal = (val: number) => (val || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workspace Diagnostics</h1>
        <p className="text-gray-500">Real-time health indicators and aggregated campaign analysis.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-l-4 border-l-blue-500 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 uppercase flex items-center justify-between">
              Total Campaigns <Target className="h-4 w-4 text-blue-500" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{diag?.campaign_count || 0}</div>
            <p className="text-sm text-gray-500 mt-1">Active tracked campaigns</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-indigo-500 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 uppercase flex items-center justify-between">
              Avg Portfolio ROAS <Activity className="h-4 w-4 text-indigo-500" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{formatDecimal(diag?.average_roas)}x</div>
            <p className="text-sm text-gray-500 mt-1">Combined efficiency</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-emerald-500 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 uppercase flex items-center justify-between">
              Total Profit <DollarSign className="h-4 w-4 text-emerald-500" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${diag?.total_profit >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {formatCurrency(diag?.total_profit)}
            </div>
            <p className="text-sm text-gray-500 mt-1">Overall portfolio net</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-red-50 border-red-100 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-red-800 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" /> Needs Attention
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-red-600">{diag?.negative_profit_campaigns || 0}</div>
            <p className="text-sm text-red-700 mt-1 font-medium">Negative Profit Campaigns</p>
          </CardContent>
        </Card>

        <Card className="bg-orange-50 border-orange-100 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-orange-800 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" /> Underperforming
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-orange-600">{diag?.low_roas_campaigns || 0}</div>
            <p className="text-sm text-orange-700 mt-1 font-medium">Low ROAS Campaigns</p>
          </CardContent>
        </Card>

        <Card className="bg-green-50 border-green-100 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-green-800 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" /> Outperforming
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-green-600">{diag?.strong_campaigns || 0}</div>
            <p className="text-sm text-green-700 mt-1 font-medium">Strong ROAS Campaigns</p>
          </CardContent>
        </Card>

        <Card className="bg-indigo-50 border-indigo-100 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-indigo-800 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" /> Ready for Review
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-indigo-600">{diag?.active_recommendations || 0}</div>
            <p className="text-sm text-indigo-700 mt-1 font-medium">Active Recommendations</p>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
