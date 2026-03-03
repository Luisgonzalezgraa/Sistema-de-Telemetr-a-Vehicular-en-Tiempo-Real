import { apiGet } from "../lib/api";

type EventsResp = { data: { ts: string; vehicle_id: string; event_type: string }[] };

export default async function EventsPage() {
  const ev = await apiGet<EventsResp>("/events/recent?limit=50");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Events</h1>
        <p className="text-sm text-muted-foreground">Recent detected events.</p>
      </div>

      <div className="rounded-2xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/30">
            <tr>
              <th className="text-left p-3">Time</th>
              <th className="text-left p-3">Vehicle</th>
              <th className="text-left p-3">Event</th>
            </tr>
          </thead>
          <tbody>
            {ev.data.map((e, idx) => (
              <tr key={idx} className="border-t">
                <td className="p-3">{e.ts}</td>
                <td className="p-3">{e.vehicle_id}</td>
                <td className="p-3 font-semibold">{e.event_type}</td>
              </tr>
            ))}
            {!ev.data.length && (
              <tr>
                <td className="p-3 text-muted-foreground" colSpan={3}>No events yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}