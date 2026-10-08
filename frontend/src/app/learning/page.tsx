"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight, CheckCircle2, TrendingUp, TrendingDown, Target, Zap } from "lucide-react";

export default function LearningCenterPage() {
  const [pastDecisions, setPastDecisions] = useState<any[]>([]);

  useEffect(() => {
    fetchLearning();
  }, []);

  const fetchLearning = async () => {
    try {
      const data = await api.getLearning();
      setPastDecisions(data);
    } catch (e) {
      console.error(e);
    }
  };

  const formatCurrency = (val: number) => `₹${(val || 0).toLocaleString()}`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Learning Center</h1>
        <p className="text-gray-500">
          Continuous evaluation of AI decision models and prediction accuracy.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-3xl font-bold text-gray-900">84%</p>
              </div>
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-500">Avg Prediction Error</p>
                <p className="text-3xl font-bold text-gray-900">±8.2%</p>
              </div>
              <div className="p-2 bg-blue-100 rounded-lg">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-500">Successful Decisions</p>
                <p className="text-3xl font-bold text-gray-900">124</p>
              </div>
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Zap className="h-5 w-5 text-indigo-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-500">Total Incremental Profit</p>
                <p className="text-3xl font-bold text-green-600">₹4.2L</p>
              </div>
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Decision Memory (Expected vs Actual)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {pastDecisions.map((dec) => (
              <div key={dec.id} className="border rounded-lg p-4 flex flex-col md:flex-row justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                <div className="flex-1 mb-4 md:mb-0">
                  <div className="text-sm text-gray-500 mb-1">{dec.id} • {dec.date}</div>
                  <div className="font-semibold text-lg">{dec.action}</div>
                  <div className="mt-2">
                    {dec.result === "OUTPERFORMED_EXPECTATION" && <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Outperformed</Badge>}
                    {dec.result === "MET_EXPECTATION" && <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Met Expectation</Badge>}
                    {dec.result === "UNDERPERFORMED_EXPECTATION" && <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">Underperformed</Badge>}
                  </div>
                </div>
                
                <div className="flex space-x-8 text-right w-full md:w-auto">
                  <div>
                    <div className="text-sm text-gray-500">Expected</div>
                    <div className="font-medium">{formatCurrency(dec.expected)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Actual</div>
                    <div className="font-medium">{formatCurrency(dec.actual)}</div>
                  </div>
                  <div className="w-24">
                    <div className="text-sm text-gray-500">Variance</div>
                    <div className={`font-bold flex items-center justify-end ${dec.variance > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {dec.variance > 0 ? '+' : ''}{((dec.variance / dec.expected) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
