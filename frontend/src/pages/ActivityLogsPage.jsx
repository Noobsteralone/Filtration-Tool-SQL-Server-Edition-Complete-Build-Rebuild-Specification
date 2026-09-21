import React, { useEffect, useState } from "react";
import { Alert, Card, Table, Tag, Typography } from "antd";
import { apiClient, friendlyError } from "../api/client.js";

export default function ActivityLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    apiClient
      .get("/api/activity-logs")
      .then((res) => setLogs(res.data))
      .catch((err) => setError(friendlyError(err, "Could not load activity logs.")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <Typography.Title level={3}>Activity Logs</Typography.Title>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Card loading={loading}>
        <Table
          rowKey="LogID"
          dataSource={logs}
          columns={[
            { title: "When", dataIndex: "CreatedAt", render: (v) => new Date(v).toLocaleString() },
            { title: "User", dataIndex: "Username" },
            { title: "Action", dataIndex: "Action" },
            { title: "Job ID", dataIndex: "JobID" },
            {
              title: "Status",
              dataIndex: "Status",
              render: (status) => <Tag color={status === "SUCCESS" ? "success" : "error"}>{status}</Tag>,
            },
            { title: "Message", dataIndex: "Message" },
          ]}
        />
      </Card>
    </div>
  );
}
