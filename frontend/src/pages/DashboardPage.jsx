import React, { useEffect, useState } from "react";
import { Alert, Card, Col, Row, Statistic, Table, Tag, Typography } from "antd";
import { Link } from "react-router-dom";
import { apiClient, friendlyError } from "../api/client.js";
import { STATUS_COLORS } from "../constants.js";

export default function DashboardPage() {
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get("/api/jobs")
      .then((res) => setJobs(res.data))
      .catch((err) => setError(friendlyError(err, "Could not load jobs.")))
      .finally(() => setLoading(false));
  }, []);

  const totals = jobs.reduce(
    (acc, job) => {
      acc.totalRows += job.TotalRows || 0;
      acc.kept += job.KeptRows || 0;
      acc.rejected += job.RejectedRows || 0;
      acc.otherTld += job.OtherTLDRows || 0;
      if (["QUEUED", "IMPORTING", "PROCESSING"].includes(job.Status)) acc.active += 1;
      return acc;
    },
    { totalRows: 0, kept: 0, rejected: 0, otherTld: 0, active: 0 }
  );

  return (
    <div>
      <Typography.Title level={3}>Dashboard</Typography.Title>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={5}>
          <Card>
            <Statistic title="Active Jobs" value={totals.active} />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic title="Rows Processed (all jobs)" value={totals.totalRows} />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic title="Kept" value={totals.kept} valueStyle={{ color: "#3f8600" }} />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic title="Rejected" value={totals.rejected} valueStyle={{ color: "#cf1322" }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="Other TLD (preserved)" value={totals.otherTld} />
          </Card>
        </Col>
      </Row>

      <Card title="Recent Jobs" loading={loading}>
        <Table
          rowKey="JobID"
          dataSource={jobs.slice(0, 10)}
          pagination={false}
          columns={[
            { title: "Job ID", dataIndex: "JobID" },
            { title: "File", dataIndex: "FileName" },
            {
              title: "Status",
              dataIndex: "Status",
              render: (status) => <Tag color={STATUS_COLORS[status] || "default"}>{status}</Tag>,
            },
            { title: "Progress", dataIndex: "ProgressPercent", render: (v) => `${Number(v || 0).toFixed(1)}%` },
            { title: "Kept", dataIndex: "KeptRows" },
            { title: "Rejected", dataIndex: "RejectedRows" },
            {
              title: "",
              render: (_, record) => <Link to={`/jobs/${record.JobID}`}>View</Link>,
            },
          ]}
        />
      </Card>
    </div>
  );
}
