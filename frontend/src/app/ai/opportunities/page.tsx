"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, ArrowRight, Target, ShieldCheck, AlertCircle } from "lucide-react";
import Link from "next/link";

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [explaining, setExplaining] = useState<Record<string, boolean>>({});
  const [explanations, setExplanations] = useState<Record<string, any>>({});

  const handleExplain = async (id: string) => {
    setExplaining(prev => ({ ...prev, [id]: true }));
    try {
      const res = await api.explainRecommendation(id);
      setExplanations(prev => ({ ...prev, [id]: res }));
    } catch (err) {
      setExplanations(prev => ({ 
        ...prev, 
        [id]: { available: false, summary: "Failed to connect to AI service." } 
      }));
    } finally {
      setExplaining(prev => ({ ...prev, [id]: false }));
    }
  };

  useEffect(() => {
    api.getOpportunities().then(data => {
      setOpportunities(data);
      setLoading(false);
    });
  }, []);

  const formatCurrency = (val: number) => `₹${(val || 0).toLocaleString()}`;

  if (loading) {
    return <div className="animate-pulse h-96 bg-gray-200 rounded-xl m-6"></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profit Optimization Opportunities</h1>
        <p className="text-gray-500">
          AI-detected business opportunities ranked by incremental profit potential.
        </p>
      </div>

      <div className="space-y-6">
        {opportunities.map((opp) => {
          
          let badgeColor = "bg-gray-100 text-gray-800 border-gray-200";
          let oppIcon = <Sparkles className="h-4 w-4 mr-1" />;
          let isRisk = opp.action_type?.includes('REVIEW') || opp.action_type?.includes('REDUCE') || opp.action_type?.includes('PAUSE');
          
          if (isRisk) {
            badgeColor = "bg-red-50 text-red-700 border-red-200";
            oppIcon = <AlertCircle className="h-4 w-4 mr-1" />;
          } else if (opp.action_type?.includes('SCALE')) {
            badgeColor = "bg-green-50 text-green-700 border-green-200";
            oppIcon = <Target className="h-4 w-4 mr-1" />;
          }

          return (
          <Card key={opp.id} className={`border shadow-sm hover:shadow-md transition-shadow ${isRisk ? 'border-red-100' : 'border-indigo-100'}`}>
            <CardHeader className={`${isRisk ? 'bg-red-50/30 border-red-50' : 'bg-indigo-50/30 border-indigo-50'} border-b pb-4`}>
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-3 mb-2">
                    <Badge variant="outline" className={badgeColor}>
                      <span className="flex items-center">{oppIcon} {opp.action_type?.replace(/_/g, ' ') || 'OPPORTUNITY'}</span>
                    </Badge>
                    <Badge className="bg-slate-800">Score: {opp.score}/100</Badge>
                    <Badge variant="outline" className="text-green-700 border-green-200 bg-green-50">
                      <ShieldCheck className="h-3 w-3 mr-1" /> High Confidence
                    </Badge>
                  </div>
                  <CardTitle className="text-xl">{opp.title}</CardTitle>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500 font-medium">Incremental Profit Potential</div>
                  <div className={`text-2xl font-bold ${opp.projected_profit && opp.projected_profit > 0 ? 'text-green-600' : 'text-gray-900'}`}>
                    {opp.projected_profit !== null ? (opp.projected_profit > 0 ? '+' : '') + formatCurrency(opp.projected_profit) : 'Unknown'}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wider">Evidence & Reasoning</h4>
                  <ul className="space-y-2">
                    {opp.evidence.map((ev: string, i: number) => (
                      <li key={i} className="flex items-start">
                        <div className="h-5 w-5 rounded-full bg-green-100 flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                          <div className="h-2 w-2 rounded-full bg-green-600"></div>
                        </div>
                        <span className="text-gray-700">{ev}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex flex-col justify-between bg-gray-50 p-6 rounded-xl border border-gray-100">
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Recommended Action</h4>
                    <p className="text-gray-700 text-lg">{opp.recommended_action}</p>
                    <p className="text-gray-500 text-sm mt-2">Target Campaign: <span className="font-medium text-gray-900">{opp.campaign_id}</span></p>
                  </div>
                  <div className="mt-6 flex justify-end gap-3">
                    <Button 
                      variant="outline"
                      className="border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                      onClick={() => handleExplain(opp.id)}
                      disabled={explaining[opp.id]}
                    >
                      <Sparkles className="mr-2 h-4 w-4" />
                      {explaining[opp.id] ? "Analyzing..." : "Explain with AI"}
                    </Button>
                    <Link href={`/optimization/simulator?recommendation_id=${opp.id}`}>
                      <Button className="bg-indigo-600 hover:bg-indigo-700">
                        Simulate <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                  
                  {explanations[opp.id] && (
                    <div className="mt-6 p-4 bg-white rounded-lg border border-indigo-100 shadow-sm text-sm text-gray-800 animate-in fade-in slide-in-from-top-2">
                      <div className="flex items-center gap-2 font-semibold text-indigo-900 mb-2">
                        <Sparkles className="h-4 w-4 text-indigo-500" /> AI Insights
                      </div>
                      
                      {!explanations[opp.id].available ? (
                        <div className="flex items-start text-gray-500 bg-gray-50 p-3 rounded">
                          <AlertCircle className="h-4 w-4 mr-2 mt-0.5" />
                          <div>
                            <p>{explanations[opp.id].summary}</p>
                            {explanations[opp.id].deterministic_summary && (
                              <p className="mt-1 font-medium">{explanations[opp.id].deterministic_summary}</p>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <p><strong>Summary:</strong> {explanations[opp.id].summary}</p>
                          <p><strong>Why it matters:</strong> {explanations[opp.id].why_it_matters}</p>
                          {explanations[opp.id].risk && (
                            <p className="text-amber-700 bg-amber-50 p-2 rounded border border-amber-100">
                              <strong>Risk Caveat:</strong> {explanations[opp.id].risk}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
          );
        })}

        {opportunities.length === 0 && (
          <div className="text-center p-12 border-2 border-dashed rounded-xl text-gray-500">
            <Target className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900">No new opportunities detected</h3>
            <p className="mt-1">Your campaigns are running optimally based on current constraints.</p>
          </div>
        )}
      </div>
    </div>
  );
}
