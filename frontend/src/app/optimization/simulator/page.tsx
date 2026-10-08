"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Calculator, CheckCircle2, AlertCircle } from "lucide-react";

function SimulatorContent() {
  const searchParams = useSearchParams();
  const recommendationId = searchParams.get("recommendation_id");

  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<string>("");
  const [proposedBudget, setProposedBudget] = useState<string>("");
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  const [recContext, setRecContext] = useState<any>(null);

  const [actionApproved, setActionApproved] = useState(false);

  useEffect(() => {
    api.getCampaigns().then(setCampaigns);
    
    if (recommendationId) {
      api.getRecommendation(recommendationId).then(rec => {
        setRecContext(rec);
        setSelectedCampaign(rec.campaign_id);
        
        // Parse recommendation to prefill budget
        const amountMatch = rec.recommended_action.match(/₹([\d.,]+)/);
        const amount = amountMatch ? parseFloat(amountMatch[1].replace(/,/g, '')) : 0;
        
        const currentBudget = rec.current_budget || 0;
        let newBudget = currentBudget;
        
        const actionLower = rec.recommended_action.toLowerCase();
        if (actionLower.includes("increase")) {
          newBudget = currentBudget + amount;
        } else if (actionLower.includes("decrease") || actionLower.includes("reduce")) {
          newBudget = Math.max(0, currentBudget - amount);
        }
        
        if (newBudget !== currentBudget || amount > 0) {
           setProposedBudget(newBudget.toString());
        }
      }).catch(err => {
         console.error("Failed to load recommendation context", err);
      });
    }
  }, [recommendationId]);

  const handleSimulate = async () => {
    if (!selectedCampaign || !proposedBudget) return;
    setLoading(true);
    setActionApproved(false);
    try {
      const result = await api.simulate({
        campaign_id: selectedCampaign,
        proposed_budget: Number(proposedBudget)
      });
      setSimulationResult(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
      if (!recommendationId || !simulationResult) return;
      
      try {
          await api.executeRecommendation(recommendationId, {
              expected_revenue: simulationResult.projected_revenue,
              expected_contribution_profit: simulationResult.projected_contribution_profit,
              expected_incremental_profit: simulationResult.incremental_contribution_profit,
              expected_roas: simulationResult.projected_roas,
              previous_budget: simulationResult.current_spend,
              approved_budget: simulationResult.proposed_spend
          });
          setActionApproved(true);
      } catch (err) {
          console.error("Error executing recommendation", err);
          alert("Failed to execute recommendation. It may have already been executed.");
      }
  }

  const formatCurrency = (val: number) => `₹${(val || 0).toLocaleString()}`;
  
  const isContradiction = recContext && simulationResult && 
    ((recContext.recommended_action.toLowerCase().includes("decrease") && simulationResult.incremental_contribution_profit < 0) || 
     (recContext.recommended_action.toLowerCase().includes("increase") && simulationResult.incremental_contribution_profit < 0));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">What-If Simulator</h1>
        <p className="text-gray-500">
          Estimated impact based on historical performance and modeled response.
        </p>
      </div>

      {recContext && (
        <Card className="border-indigo-100 bg-indigo-50/30">
          <CardContent className="p-4 flex items-start gap-4">
            <AlertCircle className="h-5 w-5 text-indigo-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-indigo-900">Simulation based on: {recContext.campaign_name}</h3>
              <div className="text-sm text-indigo-800 mt-1 space-y-1">
                <p><span className="font-medium">Current spend:</span> {formatCurrency(recContext.current_budget)}</p>
                <p><span className="font-medium">Recommended action:</span> {recContext.recommended_action}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Simulation Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Campaign</label>
              <select 
                className="w-full border rounded-md p-2 text-sm"
                value={selectedCampaign}
                onChange={(e) => setSelectedCampaign(e.target.value)}
              >
                <option value="">-- Choose Campaign --</option>
                {campaigns.map(c => (
                  <option key={c.campaign_id} value={c.campaign_id}>
                    {c.campaign_name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Proposed Spend (₹)</label>
              <Input 
                type="number" 
                placeholder="Enter new target spend"
                value={proposedBudget}
                onChange={(e) => setProposedBudget(e.target.value)}
              />
            </div>

            <Button onClick={handleSimulate} disabled={loading || !selectedCampaign || !proposedBudget} className="w-full bg-indigo-600 hover:bg-indigo-700">
              <Calculator className="mr-2 h-4 w-4" />
              Run Simulation
            </Button>
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Projected Impact</CardTitle>
          </CardHeader>
          <CardContent>
            {!simulationResult && !loading && (
              <div className="flex flex-col items-center justify-center h-48 text-gray-400">
                <Calculator className="h-12 w-12 mb-4 opacity-50" />
                <p>Run a simulation to see projected results</p>
              </div>
            )}
            {loading && (
              <div className="flex justify-center items-center h-48">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              </div>
            )}
            {simulationResult && !loading && actionApproved && (
                <div className="flex flex-col items-center justify-center h-64 bg-green-50 rounded-xl border border-green-100 p-6 text-center space-y-4">
                    <CheckCircle2 className="h-16 w-16 text-green-500" />
                    <h3 className="text-xl font-bold text-green-900">Decision approved and recorded.</h3>
                    <div className="text-green-800 text-sm space-y-1 bg-white p-4 rounded-lg shadow-sm w-full max-w-sm">
                        <p><span className="font-semibold">Campaign:</span> {campaigns.find(c => c.campaign_id === selectedCampaign)?.campaign_name}</p>
                        <p><span className="font-semibold">Previous Budget:</span> {formatCurrency(simulationResult.current_spend)}</p>
                        <p><span className="font-semibold">Approved Budget:</span> {formatCurrency(simulationResult.proposed_spend)}</p>
                        <p><span className="font-semibold">Expected Impact:</span> {simulationResult.incremental_contribution_profit > 0 ? '+' : ''}{formatCurrency(simulationResult.incremental_contribution_profit)}</p>
                        <p className="mt-2 text-green-700 border-t pt-2"><span className="font-semibold">Execution:</span> Internal decision recorded</p>
                    </div>
                </div>
            )}
            {simulationResult && !loading && !actionApproved && (
              <div className="space-y-6">
                
                {isContradiction ? (
                  <div className="p-4 bg-red-50 text-red-800 rounded-lg border border-red-200 flex gap-3 items-start">
                      <AlertCircle className="h-5 w-5 mt-0.5 text-red-600" />
                      <div>
                          <h4 className="font-bold text-red-900">Simulation validation: Review required</h4>
                          <p className="text-sm mt-1">Simulation does not support this recommendation. Proceed with caution.</p>
                      </div>
                  </div>
                ) : (
                  <div className="p-4 bg-green-50 text-green-800 rounded-lg border border-green-200 flex gap-3 items-start">
                      <CheckCircle2 className="h-5 w-5 mt-0.5 text-green-600" />
                      <div>
                          <h4 className="font-bold text-green-900">Simulation validation: Supported</h4>
                          <p className="text-sm mt-1">The expected impact aligns with the recommendation.</p>
                      </div>
                  </div>
                )}
                
                <div className="grid grid-cols-2 gap-6 mt-4">
                    <div className="border rounded-lg overflow-hidden">
                        <div className="bg-gray-100 p-3 border-b font-medium text-gray-700 text-center">CURRENT</div>
                        <div className="p-4 space-y-3">
                            <div className="flex justify-between"><span className="text-gray-500 text-sm">Spend</span><span className="font-medium">{formatCurrency(simulationResult.current_spend)}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500 text-sm">Revenue</span><span className="font-medium">{formatCurrency(simulationResult.current_revenue)}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500 text-sm">Contribution Profit</span><span className="font-medium">{formatCurrency(simulationResult.current_contribution_profit)}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500 text-sm">ROAS</span><span className="font-medium">{simulationResult.current_roas.toFixed(2)}x</span></div>
                        </div>
                    </div>
                    <div className="border border-indigo-200 rounded-lg overflow-hidden ring-1 ring-indigo-50">
                        <div className="bg-indigo-50 p-3 border-b border-indigo-100 font-medium text-indigo-900 text-center flex items-center justify-center gap-2">PROPOSED <Badge variant="secondary" className="bg-indigo-100 text-indigo-700 text-xs py-0 h-5">Projected</Badge></div>
                        <div className="p-4 space-y-3">
                            <div className="flex justify-between"><span className="text-gray-500 text-sm">Spend</span><span className="font-medium text-indigo-900">{formatCurrency(simulationResult.proposed_spend)}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500 text-sm">Revenue</span><span className="font-medium text-indigo-900">{formatCurrency(simulationResult.projected_revenue)}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500 text-sm">Contribution Profit</span><span className="font-medium text-indigo-900">{formatCurrency(simulationResult.projected_contribution_profit)}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500 text-sm">ROAS</span><span className="font-medium text-indigo-900">{simulationResult.projected_roas.toFixed(2)}x</span></div>
                        </div>
                    </div>
                </div>
                
                <div className="mt-6 border-t pt-6">
                    <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Incremental Impact</h4>
                    
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                            <div className="text-lg font-bold text-gray-900">Incremental Contribution Profit</div>
                            <div className="text-sm text-gray-500 mt-1">Compared with current campaign performance</div>
                        </div>
                        <div className={`text-3xl font-bold ${simulationResult.incremental_contribution_profit > 0 ? 'text-green-600' : simulationResult.incremental_contribution_profit < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                            {simulationResult.incremental_contribution_profit > 0 ? '+' : ''}{formatCurrency(simulationResult.incremental_contribution_profit)}
                            <div className="text-sm font-medium text-center mt-1">
                                {simulationResult.incremental_contribution_profit > 0 ? 'Expected improvement' : simulationResult.incremental_contribution_profit < 0 ? 'Expected deterioration' : 'No change'}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end pt-4">
                  <Button 
                    onClick={handleApprove} 
                    className={`${isContradiction ? 'bg-amber-600 hover:bg-amber-700' : 'bg-green-600 hover:bg-green-700'}`}
                    disabled={!recommendationId}
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    {isContradiction ? "Confirm & Execute Despite Warning" : "Approve & Execute Simulation"}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function SimulatorPage() {
  return (
    <Suspense fallback={<div>Loading simulator...</div>}>
      <SimulatorContent />
    </Suspense>
  );
}
