"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PackageOpen, AlertCircle, Upload, CheckCircle2 } from "lucide-react";

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<any>(null);

  const fetchProducts = () => {
    setLoading(true);
    api.getProducts()
      .then(data => {
        setProducts(data);
        setLoading(false);
      })
      .catch(err => {
        setError("Unable to load products. Please try again.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError("");
    setUploadSuccess(null);

    try {
      const res = await api.uploadProducts(file);
      setUploadSuccess(`Success! Created: ${res.created}, Updated: ${res.updated}`);
      fetchProducts();
    } catch (err: any) {
      setError(err.message || "Failed to upload products.");
    } finally {
      setUploading(false);
      if (event.target) event.target.value = ''; // reset input
    }
  };

  const formatCurrency = (val: number, currency: string = "USD") => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(val || 0);

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

  if (products.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <Card className="max-w-md w-full border-dashed">
          <CardContent className="flex flex-col items-center p-12 text-center">
            <PackageOpen className="h-12 w-12 text-gray-300 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900">No products yet.</h2>
            <p className="text-sm text-gray-500 mt-2 mb-6">
              Import your product catalog to start analyzing product profitability.
            </p>
            
            <div className="flex flex-col items-center">
              <label htmlFor="product-upload-empty">
                <div className="cursor-pointer bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg flex items-center transition-colors">
                  <Upload className="h-4 w-4 mr-2" />
                  {uploading ? "Uploading..." : "Upload Products CSV"}
                </div>
              </label>
              <input
                id="product-upload-empty"
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleFileUpload}
                disabled={uploading}
              />
            </div>
            
            {uploadSuccess && (
              <div className="mt-4 text-green-600 text-sm flex items-center">
                <CheckCircle2 className="h-4 w-4 mr-1" />
                {uploadSuccess}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-500">
            Analyze real profitability metrics per product based on active orders and marketing spend.
          </p>
        </div>
        <div>
            <label htmlFor="product-upload">
              <div className="cursor-pointer bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 font-medium py-2 px-4 rounded-lg flex items-center transition-colors">
                <Upload className="h-4 w-4 mr-2" />
                {uploading ? "Uploading..." : "Import CSV"}
              </div>
            </label>
            <input
              id="product-upload"
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileUpload}
              disabled={uploading}
            />
        </div>
      </div>
      
      {uploadSuccess && (
        <div className="p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg flex items-center">
          <CheckCircle2 className="h-5 w-5 mr-2" />
          {uploadSuccess}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4">Product / SKU</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Price</th>
                <th className="px-6 py-4 text-right">Cost</th>
                <th className="px-6 py-4 text-right">Units Sold</th>
                <th className="px-6 py-4 text-right">Revenue</th>
                <th className="px-6 py-4 text-right">Profit</th>
                <th className="px-6 py-4 text-right">Margin</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.product_id} className="border-b hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-gray-900">{p.name}</div>
                    <div className="text-xs text-gray-500">{p.sku}</div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant="outline" className={p.status?.toLowerCase() === 'active' ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-600'}>
                      {p.status || "Active"}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 text-right font-medium">
                    {formatCurrency(p.price, p.currency)}
                  </td>
                  <td className="px-6 py-4 text-right text-gray-600">
                    {p.cost ? formatCurrency(p.cost, p.currency) : "N/A"}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {p.units_sold || 0}
                  </td>
                  <td className="px-6 py-4 text-right font-medium">
                    {formatCurrency(p.revenue, p.currency)}
                  </td>
                  <td className={`px-6 py-4 text-right font-bold ${p.gross_profit !== null && p.gross_profit > 0 ? 'text-green-600' : p.gross_profit !== null && p.gross_profit < 0 ? 'text-red-600' : 'text-gray-500'}`}>
                    {p.gross_profit !== null ? formatCurrency(p.gross_profit, p.currency) : "N/A"}
                  </td>
                  <td className={`px-6 py-4 text-right font-semibold ${p.gross_margin > 0 ? 'text-indigo-600' : 'text-gray-500'}`}>
                    {p.gross_margin !== null ? `${p.gross_margin.toFixed(1)}%` : "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
