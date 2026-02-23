"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { Loader2 } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar
} from 'recharts'; // Assuming recharts is installed

import { api } from "@/lib/api"; // Assuming api.ts will be updated to include analytics calls
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";

// Interface for Analytics Summary data
interface AnalyticsSummaryResponse {
  total_events: number;
  events_by_type: Record<string, number>;
  provider_usage: Record<string, number>;
  // Add more summary fields as they become available from API
}

// Interface for Analytics History data
interface AnalyticsEvent {
  id: number;
  event_type: string;
  guild_id: string | null;
  channel_id: string | null;
  user_id: string | null;
  provider: string | null;
  tokens_used: number | null;
  latency_ms: number | null;
  created_at: string;
}

interface AnalyticsHistoryResponse {
  history: AnalyticsEvent[];
}


// Color palette for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF', '#FF19A0', '#19FFD4', '#FFD419'];


export default function AnalyticsPage() {
  const { data: session } = useSession();
  const { toast } = useToast();

  const [summaryData, setSummaryData] = useState<AnalyticsSummaryResponse | null>(null);
  const [historyData, setHistoryData] = useState<AnalyticsEvent[]>([]);
  const [resolvedChannelNames, setResolvedChannelNames] = useState<Record<string, string>>({});
  const [rateLimitsData, setRateLimitsData] = useState<RateLimitsResponse | null>(null);
  const [costsSummaryData, setCostsSummaryData] = useState<CostsSummaryResponse | null>(null);
  const [costsHistoryData, setCostsHistoryData] = useState<CostHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const token = (session as { accessToken?: string })?.accessToken;

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

                            const fetchAnalyticsData = async () => {
                          try {
                            setLoading(true);
                            const [summary, history, rateLimits, costsSummary, costsHistory] = await Promise.all([
                              api.getAnalyticsSummary(token),
                              api.getAnalyticsHistory(token, { limit: 1000 }), // Fetch a good amount of history for charts
                              api.getRateLimits(token),
                              api.getCostsSummary(token),
                              api.getCostsHistory(token),
                            ]);
                            setSummaryData(summary);
                            setHistoryData(history.history);
                            setRateLimitsData(rateLimits);
                            setCostsSummaryData(costsSummary);
                            setCostsHistoryData(costsHistory.cost_history);            const uniqueChannelIds = [
              ...new Set(history.history.map((event) => event.channel_id).filter(Boolean) as string[]),
            ];
            if (uniqueChannelIds.length > 0) {
              const namesResponse = await api.resolveChannels(token, uniqueChannelIds);
              setResolvedChannelNames(namesResponse.resolved_names);
            }
    
          } catch (err) {
            setError("Failed to fetch analytics data.");        console.error("Failed to fetch analytics data:", err);
        toast({
          title: "Error",
          description: "Failed to fetch analytics data.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
  }, [token, toast]);

  // --- Data Processing for Charts ---
  // Messages per day (Line Chart)
  const messagesPerDayData = historyData.reduce((acc, event) => {
    const date = event.created_at.split('T')[0]; // YYYY-MM-DD
    acc[date] = (acc[date] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const formattedMessagesPerDay = Object.entries(messagesPerDayData).map(([date, count]) => ({ date, count }));

  // Provider usage distribution (Pie Chart)
  const providerUsageData = Object.entries(summaryData?.provider_usage || {}).map(([provider, count]) => ({
    name: provider,
    value: count,
  }));

  // Top channels by activity (Bar Chart)
  // This needs guild_id and channel_id to be present in historyData
  const channelActivityData = historyData.reduce((acc, event) => {
    if (event.channel_id) {
      acc[event.channel_id] = (acc[event.channel_id] || 0) + 1;
    }
    return acc;
  }, {} as Record<string, number>);
  const formattedChannelActivity = Object.entries(channelActivityData)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5) // Top 5 channels
    .map(([channel_id, count]) => ({ channel_id, count }));

  // Average response latency (Line Chart) - placeholder for now, needs more sophisticated aggregation
  // For simplicity, we'll just show average latency per day, assuming latency is tracked for every event.
  const latencyPerDayData = historyData.reduce((acc, event) => {
    if (event.latency_ms !== null) {
      const date = event.created_at.split('T')[0];
      if (!acc[date]) {
        acc[date] = { totalLatency: 0, count: 0 };
      }
      acc[date].totalLatency += event.latency_ms;
      acc[date].count += 1;
    }
    return acc;
  }, {} as Record<string, { totalLatency: number; count: number }>);
  const formattedLatencyPerDay = Object.entries(latencyPerDayData).map(([date, data]) => ({
    date,
    averageLatency: data.count > 0 ? Math.round(data.totalLatency / data.count) : 0,
  }));


  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  if (!token) {
    return <p>Please log in to view analytics.</p>;
  }


  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Bot Analytics</h2>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Total Events</CardTitle>
            <CardDescription>Number of bot interactions recorded.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{summaryData?.total_events || 0}</p>
          </CardContent>
        </Card>

        {/* Card: Rate Limit Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Rate Limits</CardTitle>
            <CardDescription>Current bot rate limit configuration.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <p>
              Enabled:{" "}
              <span className="font-semibold">
                {rateLimitsData?.rate_limit_enabled ? "Yes" : "No"}
              </span>
            </p>
            <p>
              Per User:{" "}
              <span className="font-semibold">
                {rateLimitsData?.rate_limit_user ?? "N/A"} req/min
              </span>
            </p>
            <p>
              Per Guild:{" "}
              <span className="font-semibold">
                {rateLimitsData?.rate_limit_guild ?? "N/A"} req/min
              </span>
            </p>
          </CardContent>
        </Card>

        {/* Card: Cost Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Estimated Costs</CardTitle>
            <CardDescription>Estimated API usage costs.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <p>
              Total Cost:{" "}
              <span className="font-semibold">
                ${(costsSummaryData?.total_cost || 0).toFixed(4)}
              </span>
            </p>
            <p>
              Projected Monthly:{" "}
              <span className="font-semibold">
                ${(costsSummaryData?.projected_monthly_cost || 0).toFixed(4)}
              </span>
            </p>
            {costsSummaryData?.cost_by_provider && Object.keys(costsSummaryData.cost_by_provider).length > 0 && (
              <div className="text-sm pt-2">
                Cost by Provider:
                {Object.entries(costsSummaryData.cost_by_provider).map(([provider, cost]) => (
                  <p key={provider} className="ml-2">
                    - {provider}: ${cost.toFixed(4)}
                  </p>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Chart: Messages per day */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Messages per Day</CardTitle>
            <CardDescription>Number of events recorded daily.</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={formattedMessagesPerDay}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#8884d8" activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Chart: Provider Usage Distribution */}
        {providerUsageData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Provider Usage</CardTitle>
              <CardDescription>Distribution of AI provider usage.</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={providerUsageData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {providerUsageData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Chart: Top channels by activity */}
        {formattedChannelActivity.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Top Channels by Activity</CardTitle>
              <CardDescription>Most active channels.</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={formattedChannelActivity}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="channel_id" angle={-45} textAnchor="end" height={80} interval={0} tickFormatter={(tick) => resolvedChannelNames[tick] || tick} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Chart: Average response latency */}
        {formattedLatencyPerDay.length > 0 && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Average Response Latency (ms)</CardTitle>
              <CardDescription>Average AI response time per day.</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={formattedLatencyPerDay}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="averageLatency" stroke="#ffc658" activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Chart: Cost per Day */}
        {costsHistoryData.length > 0 && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Estimated Cost per Day</CardTitle>
              <CardDescription>Daily estimated API usage cost.</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={costsHistoryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis tickFormatter={(value) => `$${value.toFixed(2)}`} />
                  <Tooltip formatter={(value: number) => `$${value.toFixed(4)}`} />
                  <Legend />
                  <Line type="monotone" dataKey="daily_cost" stroke="#82ca9d" activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
