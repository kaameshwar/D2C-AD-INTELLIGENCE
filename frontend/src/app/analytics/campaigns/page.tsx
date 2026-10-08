"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function CampaignManagement() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCampaigns().then(data => {
      setCampaigns(data);
      setLoading(false);
    });
  }, []);

  const formatCurrency = (val: number) => `₹${(val || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Campaigns</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="animate-pulse h-64 bg-gray-100 rounded-lg"></div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Campaign</TableHead>
                  <TableHead>Platform</TableHead>
                  <TableHead className="text-right">Spend</TableHead>
                  <TableHead className="text-right">Revenue</TableHead>
                  <TableHead className="text-right">ROAS</TableHead>
                  <TableHead className="text-right">Profit</TableHead>
                  <TableHead className="text-right">Conversions</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campaigns.map((c) => {
                  const roas = c.spend > 0 ? c.revenue / c.spend : 0;
                  const profit = c.revenue - c.spend;
                  const status = roas > 2.5 ? "Healthy" : roas < 1.0 ? "At Risk" : "Watch";
                  return (
                    <TableRow key={c.campaign_id}>
                      <TableCell className="font-medium">{c.campaign_name}</TableCell>
                      <TableCell>{c.platform}</TableCell>
                      <TableCell className="text-right">{formatCurrency(c.spend)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(c.revenue)}</TableCell>
                      <TableCell className="text-right">{roas.toFixed(2)}x</TableCell>
                      <TableCell className={`text-right ${profit > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(profit)}
                      </TableCell>
                      <TableCell className="text-right">{c.conversions}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={
                          status === "Healthy" ? "bg-green-50 text-green-700 border-green-200" :
                          status === "At Risk" ? "bg-red-50 text-red-700 border-red-200" :
                          "bg-amber-50 text-amber-700 border-amber-200"
                        }>
                          {status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
