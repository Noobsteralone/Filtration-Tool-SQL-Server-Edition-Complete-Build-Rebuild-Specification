import React, { useEffect, useState } from "react";
import { Alert, Card, Input, Table, Typography } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { apiClient, friendlyError } from "../api/client.js";

export default function OtherTldMasterPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function load(search) {
    setLoading(true);
    apiClient
      .get("/api/other-tld-master", { params: { search: search || undefined, page: 1, page_size: 100 } })
      .then((res) => setRows(res.data))
      .catch((err) => setError(friendlyError(err, "Could not load Other TLD Master.")))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load("");
  }, []);

  return (
    <div>
      <Typography.Title level={3}>Other TLD Master</Typography.Title>
      <Typography.Paragraph type="secondary">
        Records whose domain falls outside the currently configured Allowed TLDs. These are preserved permanently
        rather than deleted, and are available here for reuse by future filtration jobs.
      </Typography.Paragraph>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Card>
        <Input.Search
          placeholder="Search by email, company, or name"
          allowClear
          enterButton={<SearchOutlined />}
          style={{ maxWidth: 480, marginBottom: 16 }}
          onSearch={load}
        />
        <Table
          rowKey="OtherTLDID"
          loading={loading}
          dataSource={rows}
          columns={[
            { title: "Email", dataIndex: "Email" },
            { title: "TLD", dataIndex: "TLD" },
            { title: "Name", dataIndex: "Name" },
            { title: "Company", dataIndex: "Company" },
            { title: "Source File", dataIndex: "SourceFile" },
            { title: "Added", dataIndex: "CreatedAt", render: (v) => new Date(v).toLocaleDateString() },
          ]}
        />
      </Card>
    </div>
  );
}
