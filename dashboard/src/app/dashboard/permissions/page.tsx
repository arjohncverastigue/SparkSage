"use client";

import { useState, useEffect, useMemo } from "react";
import { useSession } from "next-auth/react";
import { PlusCircle, Loader2, Trash } from "lucide-react";
import { useRouter } from "next/navigation";

import { api, CommandPermissionResponse } from "@/lib/api"; // Assuming CommandPermissionResponse is defined in api.ts
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
import { Label } from "@/components/ui/label";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";


export default function PermissionsManagementPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const { toast } = useToast();

  const [permissions, setPermissions] = useState<CommandPermissionResponse[]>([]);
  const [availableCommands, setAvailableCommands] = useState<string[]>([]); // To be fetched from bot API
  const [availableRoles, setAvailableRoles] = useState<any[]>([]); // To be fetched from bot API (id, name)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedCommand, setSelectedCommand] = useState("");
  const [selectedRole, setSelectedRole] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // TODO: Implement proper guild selection. For now, hardcode or assume a default.
  // This needs to be dynamic based on the connected bot's guilds.
  const GUILD_ID = "1474372961166299290"; // Use the actual guild ID

  const token = (session as { accessToken?: string })?.accessToken;

  // Fetch permissions, commands, and roles
  useEffect(() => {
    if (!token || !GUILD_ID) {
      setLoading(false);
      return;
    }

    const fetchPermissionsData = async () => {
      try {
        setLoading(true);
        const perms = await api.listCommandPermissions(token, GUILD_ID); // Needs to be implemented in api.ts
        setPermissions(perms);

        // TODO: Fetch available commands and roles from a bot API endpoint
        // For now, mock data:
        setAvailableCommands(["ask", "clear", "provider", "summarize", "review", "faq add", "faq list", "faq remove"]);
        // Assume bot status API can give roles
        // const botStatus = await api.getBotStatus(token);
        // if (botStatus && botStatus.guilds) {
        //   const currentGuild = botStatus.guilds.find(g => g.id === GUILD_ID);
        //   if (currentGuild) {
        //     setAvailableRoles(currentGuild.roles); // Assuming roles are part of guild object
        //   }
        // }
        // Mock roles for now:
        setAvailableRoles([
            { id: "12345", name: "Admin" },
            { id: "67890", name: "Member" },
            { id: "54321", name: "Moderator" },
        ]);


      } catch (err) {
        setError("Failed to fetch permissions data.");
        console.error("Failed to fetch permissions data:", err);
        toast({
          title: "Error",
          description: "Failed to fetch permissions data.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchPermissionsData();
  }, [token, GUILD_ID, toast]);


  const handleAddPermission = async () => {
    if (!token || !GUILD_ID || !selectedCommand || !selectedRole) {
      toast({
        title: "Error",
        description: "Please select a command and a role.",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      const createdPerm = await api.createCommandPermission(token, { // Needs to be implemented in api.ts
        command_name: selectedCommand,
        guild_id: GUILD_ID,
        role_id: selectedRole,
      });
      setPermissions((prev) => [...prev, createdPerm]);
      setSelectedCommand("");
      setSelectedRole("");
      toast({
        title: "Success",
        description: "Permission added successfully!",
      });
    } catch (err) {
      setError("Failed to add permission.");
      console.error("Failed to add permission:", err);
      toast({
        title: "Error",
        description: "Failed to add permission.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePermission = async (permission: CommandPermissionResponse) => {
    if (!token || !GUILD_ID) {
      toast({
        title: "Error",
        description: "Authentication token or Guild ID is missing.",
        variant: "destructive",
      });
      return;
    }

    if (!confirm(`Are you sure you want to remove the restriction for command '${permission.command_name}' for role '${availableRoles.find(r => r.id === permission.role_id)?.name || permission.role_id}'?`)) {
      return;
    }

    try {
      await api.deleteCommandPermission(token, permission.command_name, GUILD_ID, permission.role_id); // Needs to be implemented in api.ts
      setPermissions((prev) => prev.filter((p) => p.command_name !== permission.command_name || p.role_id !== permission.role_id));
      toast({
        title: "Success",
        description: "Permission removed successfully!",
      });
    } catch (err) {
      setError("Failed to delete permission.");
      console.error("Failed to delete permission:", err);
      toast({
        title: "Error",
        description: "Failed to delete permission.",
        variant: "destructive",
      });
    }
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  if (!token) {
    return <p>Please log in to manage permissions.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Command Permissions</h2>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" /> Add Permission
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Add Command Permission</DialogTitle>
              <DialogDescription>
                Restrict a command to a specific role.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="command" className="text-right">
                  Command
                </Label>
                <div className="col-span-3">
                  <Select onValueChange={setSelectedCommand} value={selectedCommand}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a command" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableCommands.map((cmd) => (
                        <SelectItem key={cmd} value={cmd}>
                          /{cmd}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="role" className="text-right">
                  Role
                </Label>
                <div className="col-span-3">
                  <Select onValueChange={setSelectedRole} value={selectedRole}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a role" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableRoles.map((role) => (
                        <SelectItem key={role.id} value={role.id}>
                          {role.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleAddPermission} disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add Permission
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Existing Permissions</CardTitle>
          <CardDescription>
            Manage which roles are required to use specific commands.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Command</TableHead>
                <TableHead>Required Role</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {permissions.map((perm) => (
                <TableRow key={`${perm.command_name}-${perm.role_id}`}>
                  <TableCell className="font-medium">/{perm.command_name}</TableCell>
                  <TableCell>
                    {availableRoles.find(r => r.id === perm.role_id)?.name || `ID: ${perm.role_id}`}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeletePermission(perm)}
                    >
                      <Trash className="h-4 w-4" />
                    </Button>
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
