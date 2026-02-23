"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { PlusCircle, Loader2, Trash, PlayCircle, PauseCircle } from "lucide-react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api"; // Assuming api.ts will be updated to include plugin calls
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from "@/components/ui/dialog";

// Interface for Plugin data
interface PluginResponse {
  name: string;
  version: string;
  author: string | null;
  description: string | null;
  cog_path: string;
  manifest_path: string; // Not used for display but part of the backend model
  enabled: boolean;
  installed_at: string;
}

export default function PluginManagementPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const { toast } = useToast();

  const [plugins, setPlugins] = useState<PluginResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newPluginName, setNewPluginName] = useState("");
  const [newVersion, setNewVersion] = useState("");
  const [newAuthor, setNewAuthor] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newCogPath, setNewCogPath] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const token = (session as { accessToken?: string })?.accessToken;

  async function fetchPlugins() {
    if (!token) return;
    try {
      setLoading(true);
      const response = await api.listPlugins(token);
      setPlugins(response.plugins);
    } catch (err) {
      setError("Failed to fetch plugins.");
      console.error("Failed to fetch plugins:", err);
      toast({
        title: "Error",
        description: "Failed to fetch plugins.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchPlugins();
  }, [token, toast]);

  const handleInstallPlugin = async () => {
    if (!token || !newPluginName || !newVersion || !newCogPath) {
      toast({
        title: "Error",
        description: "Please fill in all required fields for the new plugin (Name, Version, Cog Path).",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      const manifest = {
        name: newPluginName,
        version: newVersion,
        author: newAuthor,
        description: newDescription,
        cog: newCogPath,
      };
      await api.installPlugin(token, manifest);
      setNewPluginName("");
      setNewVersion("");
      setNewAuthor("");
      setNewDescription("");
      setNewCogPath("");
      toast({
        title: "Success",
        description: "Plugin installed successfully! You can now enable it.",
      });
      fetchPlugins(); // Refresh list
    } catch (err: any) {
      setError("Failed to install plugin.");
      console.error("Failed to install plugin:", err);
      toast({
        title: "Error",
        description: err.message || "Failed to install plugin.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleEnableDisablePlugin = async (pluginName: string, enable: boolean) => {
    if (!token) {
      toast({
        title: "Error",
        description: "Authentication token is missing.",
        variant: "destructive",
      });
      return;
    }

    try {
      if (enable) {
        await api.enablePlugin(token, pluginName);
        toast({
          title: "Success",
          description: `Plugin '${pluginName}' enabled successfully!`,
        });
      } else {
        await api.disablePlugin(token, pluginName);
        toast({
          title: "Success",
          description: `Plugin '${pluginName}' disabled successfully!`,
        });
      }
      fetchPlugins(); // Refresh list
    } catch (err: any) {
      setError(`Failed to ${enable ? "enable" : "disable"} plugin.`);
      console.error(`Failed to ${enable ? "enable" : "disable"} plugin:`, err);
      toast({
        title: "Error",
        description: err.message || `Failed to ${enable ? "enable" : "disable"} plugin.`,
        variant: "destructive",
      });
    }
  };

  const handleDeletePlugin = async (pluginName: string) => {
    if (!token) {
      toast({
        title: "Error",
        description: "Authentication token is missing.",
        variant: "destructive",
      });
      return;
    }

    if (!confirm(`Are you sure you want to delete plugin '${pluginName}'? This action cannot be undone.`)) {
      return;
    }

    try {
      await api.deletePlugin(token, pluginName);
      toast({
        title: "Success",
        description: `Plugin '${pluginName}' deleted successfully!`,
      });
      fetchPlugins(); // Refresh list
    } catch (err: any) {
      setError("Failed to delete plugin.");
      console.error("Failed to delete plugin:", err);
      toast({
        title: "Error",
        description: err.message || "Failed to delete plugin.",
        variant: "destructive",
      });
    }
  };


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
    return <p>Please log in to manage plugins.</p>;
  }


  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Plugin Management</h2>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" /> Install New Plugin
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Install New Plugin</DialogTitle>
              <DialogDescription>
                Register a new plugin. The plugin's code must already be present in the `plugins/` directory.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="plugin-name" className="text-right">
                  Name
                </Label>
                <Input
                  id="plugin-name"
                  value={newPluginName}
                  onChange={(e) => setNewPluginName(e.target.value)}
                  className="col-span-3"
                  placeholder="e.g., trivia"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="plugin-version" className="text-right">
                  Version
                </Label>
                <Input
                  id="plugin-version"
                  value={newVersion}
                  onChange={(e) => setNewVersion(e.target.value)}
                  className="col-span-3"
                  placeholder="e.g., 1.0.0"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="plugin-author" className="text-right">
                  Author
                </Label>
                <Input
                  id="plugin-author"
                  value={newAuthor}
                  onChange={(e) => setNewAuthor(e.target.value)}
                  className="col-span-3"
                  placeholder="e.g., John Doe"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="plugin-description" className="text-right">
                  Description
                </Label>
                <Textarea
                  id="plugin-description"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="col-span-3"
                  rows={3}
                  placeholder="A short description of the plugin."
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="plugin-cog-path" className="text-right">
                  Cog Path
                </Label>
                <Input
                  id="plugin-cog-path"
                  value={newCogPath}
                  onChange={(e) => setNewCogPath(e.target.value)}
                  className="col-span-3"
                  placeholder="e.g., plugins.trivia.trivia_cog"
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleInstallPlugin} disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Install Plugin
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Installed Plugins</CardTitle>
          <CardDescription>
            Manage your bot's community-contributed extensions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[150px]">Name</TableHead>
                <TableHead className="w-[80px]">Version</TableHead>
                <TableHead className="w-[120px]">Author</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="w-[100px] text-center">Status</TableHead>
                <TableHead className="w-[150px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plugins.map((plugin) => (
                <TableRow key={plugin.name}>
                  <TableCell className="font-medium">{plugin.name}</TableCell>
                  <TableCell>{plugin.version}</TableCell>
                  <TableCell>{plugin.author || "N/A"}</TableCell>
                  <TableCell>{plugin.description ? (plugin.description.length > 50 ? `${plugin.description.slice(0, 50)}...` : plugin.description) : "N/A"}</TableCell>
                  <TableCell className="text-center">
                    {plugin.enabled ? (
                      <span className="text-green-500">Enabled</span>
                    ) : (
                      <span className="text-red-500">Disabled</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEnableDisablePlugin(plugin.name, !plugin.enabled)}
                      >
                        {plugin.enabled ? <PauseCircle className="h-4 w-4" /> : <PlayCircle className="h-4 w-4" />}
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeletePlugin(plugin.name)}
                      >
                        <Trash className="h-4 w-4" />
                      </Button>
                    </div>
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