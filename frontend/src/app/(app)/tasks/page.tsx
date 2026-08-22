"use client";

import { useEffect, useState } from "react";
import { Check, Trash2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PriorityBadge } from "@/components/priority-badge";
import { tasks, type Task } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

const FILTERS = [
  { label: "All", value: undefined },
  { label: "Pending", value: false },
  { label: "Completed", value: true },
];

export default function TasksPage() {
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  const [completedFilter, setCompletedFilter] = useState<boolean | undefined>(false);
  const [loading, setLoading] = useState(true);
  const [newTitle, setNewTitle] = useState("");
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await tasks.list({ completed: completedFilter });
      setAllTasks(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [completedFilter]);

  async function handleComplete(id: string) {
    await tasks.update(id, { completed: true });
    toast({ title: "Task completed", variant: "success" });
    await load();
  }

  async function handleDelete(id: string) {
    await tasks.delete(id);
    toast({ title: "Task deleted", variant: "default" });
    await load();
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      await tasks.create({ title: newTitle.trim() });
      setNewTitle("");
      toast({ title: "Task created", variant: "success" });
      await load();
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Tasks</h1>
        <div className="flex gap-1 rounded-lg border p-1">
          {FILTERS.map(({ label, value }) => (
            <button
              key={label}
              onClick={() => setCompletedFilter(value)}
              className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                completedFilter === value
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Quick create */}
      <form onSubmit={handleCreate} className="flex gap-2">
        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="Add a new task…"
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <Button type="submit" disabled={creating || !newTitle.trim()} className="gap-2">
          <Plus className="h-4 w-4" /> Add
        </Button>
      </form>

      {/* Task list */}
      <div className="space-y-2">
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : allTasks.length === 0 ? (
          <p className="text-sm text-muted-foreground">No tasks found.</p>
        ) : (
          allTasks.map((task) => (
            <div
              key={task.id}
              className={`flex items-center gap-3 rounded-lg border bg-card p-3 transition-colors ${
                task.completed ? "opacity-60" : ""
              }`}
            >
              <button
                onClick={() => !task.completed && handleComplete(task.id)}
                disabled={task.completed}
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                  task.completed
                    ? "border-green-500 bg-green-500"
                    : "border-muted-foreground hover:border-primary"
                }`}
              >
                {task.completed && <Check className="h-3 w-3 text-white" />}
              </button>

              <div className="flex-1 min-w-0">
                <p className={`font-medium ${task.completed ? "line-through text-muted-foreground" : ""}`}>
                  {task.title}
                </p>
                {task.deadline && (
                  <p className="text-xs text-muted-foreground">
                    Due: {new Date(task.deadline).toLocaleDateString()}
                  </p>
                )}
              </div>

              <div className="flex shrink-0 items-center gap-2">
                <Badge variant="outline" className="capitalize text-xs hidden sm:inline-flex">
                  {task.action_type}
                </Badge>
                <PriorityBadge priority={task.priority} />
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={() => handleDelete(task.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
