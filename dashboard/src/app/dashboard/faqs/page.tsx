"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { PlusCircle, Loader2, Trash } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { api, FAQResponse } from "@/lib/api";
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

export default function FAQManagementPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const { toast } = useToast();

  const [faqs, setFaqs] = useState<FAQResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newQuestion, setNewQuestion] = useState("");
  const [newAnswer, setNewAnswer] = useState("");
  const [newKeywords, setNewKeywords] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // TODO: Implement proper guild selection. For now, hardcode or assume a default.
  // This needs to be dynamic based on the connected bot's guilds.
  const GUILD_ID = "1474372961166299290"; // Replace with actual guild ID

  const token = (session as { accessToken?: string })?.accessToken;

  useEffect(() => {
    if (!token) {
      // If no token, we might be unauthenticated or still loading session
      // Redirect or show a message if necessary
      setLoading(false);
      return;
    }

    const fetchFaqs = async () => {
      try {
        setLoading(true);
        // Assuming API expects guild_id as query param for listing FAQs
        const response = await api.listFaqs(token, GUILD_ID); // Needs to be implemented in api.ts
        setFaqs(response);
      } catch (err) {
        setError("Failed to fetch FAQs.");
        console.error("Failed to fetch FAQs:", err);
        toast({
          title: "Error",
          description: "Failed to fetch FAQs.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchFaqs();
  }, [token, toast]);

  const handleAddFaq = async () => {
    if (!token || !GUILD_ID || !newQuestion || !newAnswer || !newKeywords) {
      toast({
        title: "Error",
        description: "Please fill in all fields for the new FAQ.",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      const createdFaq = await api.createFaq(token, GUILD_ID, { // Needs to be implemented in api.ts
        question: newQuestion,
        answer: newAnswer,
        match_keywords: newKeywords,
      });
      setFaqs((prev) => [...prev, createdFaq]);
      setNewQuestion("");
      setNewAnswer("");
      setNewKeywords("");
      toast({
        title: "Success",
        description: "FAQ added successfully!",
      });
    } catch (err) {
      setError("Failed to add FAQ.");
      console.error("Failed to add FAQ:", err);
      toast({
        title: "Error",
        description: "Failed to add FAQ.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteFaq = async (faqId: number) => {
    if (!token || !GUILD_ID) {
      toast({
        title: "Error",
        description: "Authentication token or Guild ID is missing.",
        variant: "destructive",
      });
      return;
    }

    if (!confirm("Are you sure you want to delete this FAQ?")) {
      return;
    }

    try {
      await api.deleteFaq(token, GUILD_ID, faqId); // Needs to be implemented in api.ts
      setFaqs((prev) => prev.filter((faq) => faq.id !== faqId));
      toast({
        title: "Success",
        description: "FAQ deleted successfully!",
      });
    } catch (err) {
      setError("Failed to delete FAQ.");
      console.error("Failed to delete FAQ:", err);
      toast({
        title: "Error",
        description: "Failed to delete FAQ.",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return <Loader2 className="h-8 w-8 animate-spin" />;
  }

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  if (!token) {
    return <p>Please log in to manage FAQs.</p>;
  }


  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">FAQ Management</h2>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" /> Add New FAQ
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Add New FAQ</DialogTitle>
              <DialogDescription>
                Add a new frequently asked question for your bot.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="question" className="text-right">
                  Question
                </Label>
                <Input
                  id="question"
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="answer" className="text-right">
                  Answer
                </Label>
                <Textarea
                  id="answer"
                  value={newAnswer}
                  onChange={(e) => setNewAnswer(e.target.value)}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="keywords" className="text-right">
                  Keywords
                </Label>
                <Input
                  id="keywords"
                  value={newKeywords}
                  onChange={(e) => setNewKeywords(e.target.value)}
                  placeholder="comma,separated,keywords"
                  className="col-span-3"
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleAddFaq} disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add FAQ
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Existing FAQs</CardTitle>
          <CardDescription>
            Manage the FAQs that your bot can automatically answer.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">ID</TableHead>
                <TableHead>Question</TableHead>
                <TableHead>Answer</TableHead>
                <TableHead>Keywords</TableHead>
                <TableHead className="text-center">Used</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {faqs.map((faq) => (
                <TableRow key={faq.id}>
                  <TableCell className="font-medium">{faq.id}</TableCell>
                  <TableCell>{faq.question}</TableCell>
                  <TableCell>{faq.answer.length > 50 ? `${faq.answer.slice(0, 50)}...` : faq.answer}</TableCell>
                  <TableCell>{faq.match_keywords}</TableCell>
                  <TableCell className="text-center">{faq.times_used}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeleteFaq(faq.id)}
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
