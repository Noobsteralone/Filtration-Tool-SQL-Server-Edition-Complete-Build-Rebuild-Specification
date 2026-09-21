import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Popconfirm, Table, Tag, Typography, message } from "antd";
import { Link } from "react-router-dom";
import { apiClient, friendlyError } from "../api/client.js";
import { STATUS_COLORS } from "../constants.js";

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function load() {
    setLoading(true);
    apiClient
      .get("/api/jobs")
      .then((res) => setJobs(res.data))
      .catch((err) => setError(friendlyError(err, "Could not load jobs.")))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  async function cancelJob(jobId) {
    try {
      await apiClient.post(`/api/jobs/${jobId}/cancel`);
      message.success("Cancellation requested.");
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not cancel this job."));
    }
  }

  async function retryJob(jobId) {
    try {
      await apiClient.post(`/api/jobs/${jobId}/retry`);
      message.success("Job re-queued.");
      load();
    } catch (err) {
      message.error(friendlyError(err, "Could not retry this job."));
    }
  }

  return (
    <div>
      <Typography.Title level={3}>Jobs</Typography.Title>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Card>
        <Table
          rowKey="JobID"
          loading={loading}
          dataSource={jobs}
          columns={[
            { title: "Job ID", dataIndex: "JobID" },
            { title: "Type", dataIndex: "JobType" },
            { title: "File", dataIndex: "FileName" },
            {
              title: "Status",
              dataIndex: "Status",
              render: (status) => <Tag color={STATUS_COLORS[status] || "default"}>{status}</Tag>,
            },
            { title: "Current Step", dataIndex: "CurrentStep" },
            { title: "Progress", dataIndex: "ProgressPercent", render: (v) => `${Number(v || 0).toFixed(1)}%` },
            { title: "Created", dataIndex: "CreatedAt", render: (v) => new Date(v).toLocaleString() },
            {
              title: "Actions",
              render: (_, record) => (
                <span style={{ display: "flex", gap: 8 }}>
                  <Link to={`/jobs/${record.JobID}`}>View</Link>
                  {["QUEUED", "IMPORTING", "PROCESSING"].includes(record.Status) && (
                    <Popconfirm title="Cancel this job?" onConfirm={() => cancelJob(record.JobID)}>
                      <Button size="small" danger>
                        Cancel
                      </Button>
                    </Popconfirm>
                  )}
                  {["FAILED", "CANCELLED"].includes(record.Status) && (
                    <Button size="small" onClick={() => retryJob(record.JobID)}>
                      Retry
                    </Button>
                  )}
                </span>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
