"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { UploadCloud, CheckCircle2, Building2 } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuth();
  const [campaignFile, setCampaignFile] = useState<File | null>(null);
  const [productFile, setProductFile] = useState<File | null>(null);
  const [orderFile, setOrderFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleUpload = async (type: 'campaigns' | 'products' | 'orders') => {
    const file = type === 'campaigns' ? campaignFile : type === 'products' ? productFile : orderFile;
    if (!file) return;
    
    setLoading(true);
    setError("");
    setMessage("");
    try {
      let res;
      if (type === 'campaigns') {
        res = await api.uploadCampaigns(file);
        setCampaignFile(null);
      } else if (type === 'products') {
        res = await api.uploadProducts(file);
        setProductFile(null);
      } else if (type === 'orders') {
        res = await api.uploadOrders(file);
        setOrderFile(null);
      }
      
      setMessage(`Successfully imported ${res.rows_imported} rows!`);
    } catch (e: any) {
      setError(e.message || `Failed to import ${type} CSV. Please check the format.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workspace Settings & Data Ingestion</h1>
        <p className="text-gray-500">Manage {user?.organization_name} data sources.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Building2 className="h-5 w-5" /> Workspace Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <p className="text-sm text-gray-500">Organization Name</p>
              <p className="font-medium text-gray-900">{user?.organization_name}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-gray-500">Organization ID</p>
              <p className="text-sm font-mono text-gray-700 bg-gray-100 p-2 rounded">{user?.organization_id}</p>
            </div>
            <div className="text-sm text-green-600 flex items-center mt-4">
              <CheckCircle2 className="h-4 w-4 mr-1" /> Workspace is active and isolated
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><UploadCloud className="h-5 w-5" /> Import Data</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            
            <div className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-900">Campaign Performance</p>
                <p className="text-xs text-gray-500">CSV must include: campaign_id, spend, revenue, clicks, conversions</p>
                <div className="flex gap-2">
                  <Input 
                    type="file" 
                    accept=".csv"
                    onChange={(e) => setCampaignFile(e.target.files?.[0] || null)}
                    className="flex-1"
                  />
                  <Button onClick={() => handleUpload('campaigns')} disabled={!campaignFile || loading} className="bg-indigo-600 hover:bg-indigo-700">
                    {loading ? "..." : "Sync Campaigns"}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-900">Products & Costs</p>
                <p className="text-xs text-gray-500">CSV must include: sku, name, price, cost</p>
                <div className="flex gap-2">
                  <Input 
                    type="file" 
                    accept=".csv"
                    onChange={(e) => setProductFile(e.target.files?.[0] || null)}
                    className="flex-1"
                  />
                  <Button onClick={() => handleUpload('products')} disabled={!productFile || loading} className="bg-indigo-600 hover:bg-indigo-700">
                    {loading ? "..." : "Sync Products"}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-900">Order Intelligence</p>
                <p className="text-xs text-gray-500">CSV must include: order_id, product_sku, customer_id, quantity, total</p>
                <div className="flex gap-2">
                  <Input 
                    type="file" 
                    accept=".csv"
                    onChange={(e) => setOrderFile(e.target.files?.[0] || null)}
                    className="flex-1"
                  />
                  <Button onClick={() => handleUpload('orders')} disabled={!orderFile || loading} className="bg-indigo-600 hover:bg-indigo-700">
                    {loading ? "..." : "Sync Orders"}
                  </Button>
                </div>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-100 rounded-md text-sm text-red-600 font-medium">
                {error}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {message && (
        <div className="p-4 bg-green-50 text-green-700 rounded-lg border border-green-100 font-medium flex items-center">
          <CheckCircle2 className="h-5 w-5 mr-2" />
          {message}
        </div>
      )}
    </div>
  );
}
