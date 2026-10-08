"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function ChannelsPage() {
  const [channels, setChannels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getChannels().then(data => {
      setChannels(data);
      setLoading(false);
    });
  }, []);

  const formatCurrency = (val: number) => `₹${(val || 0).toLocaleString()}`;

  if (loading) return <div className="animate-pulse h-96 bg-gray-200 rounded-xl m-6"></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Channels Performance</h1>
        <p className="text-gray-500">Analyze performance across all advertising platforms.</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={channels}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="platform" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} tickFormatter={(v) => `₹${v/1000}k`} />
                <Tooltip formatter={(v: any) => `₹${v}`} />
                <Bar dataKey="revenue" fill="#4f46e5" radius={[4, 4, 0, 0]} name="Revenue" />
                <Bar dataKey="spend" fill="#ef4444" radius={[4, 4, 0, 0]} name="Spend" />
                <Bar dataKey="profit" fill="#10b981" radius={[4, 4, 0, 0]} name="Profit" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Platform Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Platform</TableHead>
                <TableHead className="text-right">Spend</TableHead>
                <TableHead className="text-right">Revenue</TableHead>
                <TableHead className="text-right">ROAS</TableHead>
                <TableHead className="text-right">Profit</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {channels.map((c) => (
                <TableRow key={c.platform}>
                  <TableCell className="font-medium">{c.platform}</TableCell>
                  <TableCell className="text-right">{formatCurrency(c.spend)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(c.revenue)}</TableCell>
                  <TableCell className="text-right">{c.roas.toFixed(2)}x</TableCell>
                  <TableCell className={`text-right ${c.profit > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(c.profit)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
