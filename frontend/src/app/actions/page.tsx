"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircle2, PlayCircle, Clock, RefreshCw } from "lucide-react";
import Link from "next/link";

export default function ActionCenterPage() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [syncing, setSyncing] = useState(false);
  
  useEffect(() => {
    fetchRecs();
  }, []);

  const fetchRecs = async () => {
    const data = await api.getRecommendations();
    setRecommendations(data);
  };

  const handleApprove = async (id: string) => {
    await api.approveRecommendation(id);
    // Optimistic update
    setRecommendations(recs => recs.map(r => r.id === id ? { ...r, status: "Approved" } : r));
  };

  const handleExecute = async (id: string) => {
    await api.executeRecommendation(id);
    // Optimistic update
    setRecommendations(recs => recs.map(r => r.id === id ? { ...r, status: "Executed" } : r));
  };

  const handleDemoSync = async () => {
    setSyncing(true);
    try {
      await api.demoSync();
      await fetchRecs();
    } finally {
      setSyncing(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Pending': return <Badge variant="outline" className="bg-amber-50 text-amber-600 border-amber-200">Pending</Badge>;
      case 'Approved': return <Badge variant="outline" className="bg-blue-50 text-blue-600 border-blue-200">Approved</Badge>;
      case 'Executed': return <Badge variant="outline" className="bg-green-50 text-green-600 border-green-200">Executed</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Action Center</h1>
          <p className="text-gray-500">
            Review, approve, and execute AI-generated profit optimization decisions.
          </p>
        </div>
        <Button onClick={handleDemoSync} disabled={syncing} variant="outline" className="border-indigo-200 text-indigo-700 bg-indigo-50 hover:bg-indigo-100">
          <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing...' : 'DEMO CONTINUOUS SYNC'}
        </Button>
      </div>

      <Tabs defaultValue="pending" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="approved">Approved</TabsTrigger>
          <TabsTrigger value="executed">Executed</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
        </TabsList>
        
        {['pending', 'approved', 'executed', 'monitoring'].map((tab) => (
          <TabsContent key={tab} value={tab}>
            <div className="space-y-4">
              {recommendations.filter(r => r.status.toLowerCase() === tab || (tab === 'pending' && !['approved', 'executed', 'monitoring'].includes(r.status.toLowerCase()))).length === 0 ? (
                <div className="text-center p-8 border border-dashed rounded-lg text-gray-500">
                  No {tab} actions currently.
                </div>
              ) : (
                recommendations.filter(r => r.status.toLowerCase() === tab || (tab === 'pending' && !['approved', 'executed', 'monitoring'].includes(r.status.toLowerCase()))).map(rec => (
                  <Card key={rec.id} className="overflow-hidden">
                    <div className="flex flex-col md:flex-row">
                      <div className="p-6 flex-1">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <div className="text-sm font-semibold text-indigo-600 mb-1">{rec.campaign_id}</div>
                            <h3 className="text-lg font-bold">{rec.action}</h3>
                          </div>
                          {getStatusBadge(rec.status)}
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <div className="text-xs text-gray-500 uppercase tracking-wide">Budget Change</div>
                            <div className="font-semibold text-gray-900">₹{rec.budget_change.toLocaleString()}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 uppercase tracking-wide">Expected Impact</div>
                            <div className="font-semibold text-green-600">{rec.expected_impact}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 uppercase tracking-wide">Confidence</div>
                            <div className="font-semibold text-indigo-600">{rec.confidence}</div>
                          </div>
                        </div>

                        <div className="bg-gray-50 p-3 rounded-md text-sm text-gray-600">
                          <span className="font-semibold">Reason:</span> {rec.reason}
                        </div>
                      </div>
                      
                      <div className="bg-gray-50 p-6 md:w-64 border-t md:border-t-0 md:border-l flex flex-col justify-center space-y-3">
                        {rec.status === 'Pending' && (
                          <Button onClick={() => handleApprove(rec.id)} className="w-full bg-blue-600 hover:bg-blue-700">
                            <CheckCircle2 className="mr-2 h-4 w-4" /> Approve Action
                          </Button>
                        )}
                        {rec.status === 'Approved' && (
                          <Button onClick={() => handleExecute(rec.id)} className="w-full bg-indigo-600 hover:bg-indigo-700">
                            <PlayCircle className="mr-2 h-4 w-4" /> Execute Simulation
                          </Button>
                        )}
                        {rec.status === 'Executed' && (
                          <Link href="/learning" passHref legacyBehavior>
                            <Button variant="outline" className="w-full">
                              <Clock className="mr-2 h-4 w-4" /> View in Learning
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
