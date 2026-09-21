import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Descriptions, Progress, Table, Tag, Typography } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { apiClient, friendlyError } from "../api/client.js";
import { REASON_CODE_LABELS, STATUS_COLORS } from "../constants.js";

const ACTIVE_STATUSES = ["QUEUED", "IMPORTING", "PROCESSING", "CANCELLING"];

export default function JobDetailPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  function load() {
    apiClient
      .get(`/api/jobs/${jobId}`)
      .then((res) => setJob(res.data))
      .catch((err) => setError(friendlyError(err, "Could not load this job.")));
    apiClient
      .get(`/api/jobs/${jobId}/results`)
      .then((res) => setResults(res.data))
      .catch(() => {});
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  if (error) return <Alert type="error" message={error} />;
  if (!job) return null;

  const isActive = ACTIVE_STATUSES.includes(job.Status);
  const elapsedSeconds =
    job.StartTime && (job.EndTime || isActive)
      ? Math.round((new Date(job.EndTime || Date.now()) - new Date(job.StartTime)) / 1000)
      : null;

  return (
    <div>
      <Typography.Title level={3}>Job #{job.JobID}</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="File">{job.FileName}</Descriptions.Item>
          <Descriptions.Item label="Type">{job.JobType}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={STATUS_COLORS[job.Status] || "default"}>{job.Status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Current Step">{job.CurrentStep || "-"}</Descriptions.Item>
          <Descriptions.Item label="Elapsed Time">{elapsedSeconds != null ? `${elapsedSeconds}s` : "-"}</Descriptions.Item>
          <Descriptions.Item label="Total Rows">{job.TotalRows}</Descriptions.Item>
          <Descriptions.Item label="Kept">{job.KeptRows}</Descriptions.Item>
          <Descriptions.Item label="Rejected">{job.RejectedRows}</Descriptions.Item>
          <Descriptions.Item label="Other TLD">{job.OtherTLDRows}</Descriptions.Item>
        </Descriptions>
        {isActive && (
          <Progress percent={Number(job.ProgressPercent || 0).toFixed(1)} status="active" style={{ marginTop: 16 }} />
        )}
        {job.Status === "FAILED" && job.ErrorMessage && (
          <Alert type="error" message="Job Failed" description={job.ErrorMessage} style={{ marginTop: 16 }} />
        )}
      </Card>

      {job.Status === "COMPLETED" && (
        <Card title="Report Summary" extra={<DownloadReportButton jobId={job.JobID} />}>
          <Table
            rowKey="ReasonCode"
            dataSource={results}
            pagination={false}
            columns={[
              { title: "Category", dataIndex: "ReasonCode", render: (code) => REASON_CODE_LABELS[code] || code },
              { title: "Row Count", dataIndex: "RowCount" },
              {
                title: "Download",
                render: (_, record) =>
                  record.OutputFilePath ? (
                    <a href={`/api/jobs/${job.JobID}/download/${record.ReasonCode}`} target="_blank" rel="noreferrer">
                      <DownloadOutlined /> CSV
                    </a>
                  ) : (
                    "-"
                  ),
              },
            ]}
          />
        </Card>
      )}
    </div>
  );
}

function DownloadReportButton({ jobId }) {
  return (
    <Button icon={<DownloadOutlined />} href={`/api/jobs/${jobId}/download/report`} target="_blank">
      Download Consolidated Excel Report
    </Button>
  );
}
