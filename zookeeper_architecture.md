graph TD

    %% ── Project Metadata ──────────────────────────────────────────────
    subgraph META["Project Infrastructure (confidence: 0.85)"]
        ASF[".asf.yaml\nProject Metadata"]
        README["README / README_packaging\nDocs & Build Instructions"]
        TYPOS[".typos.toml\nTypo Config"]
        MERGE["zk-merge-pr.py\nPR Automation (GitHub/JIRA)"]
        VERSION["Info.java / VersionInfoMain\nVersion Info"]
        COMPAT["check_compatibility.py\nJava API Compat Check"]
    end

    %% ── ZooKeeper Server Core (inferred from test targets) ────────────
    subgraph SERVER["ZooKeeper Server Core (confidence: 0.80)"]
        ZKSERVER["ZooKeeper Server\n(Standalone / Quorum)"]
        QUORUM["Quorum / Leader Election"]
        SESSION["Session Manager"]
        DATASTORE["Data Tree / ZNode Store"]
        TXNLOG["Transaction Log"]
        CNXN["ServerCnxn\n(NIO / Netty)"]
    end

    %% ── Security / Auth Layer ─────────────────────────────────────────
    subgraph AUTH["Authentication & Security (confidence: 0.90)"]
        SASL["SASL Auth\n(Digest / Kerberos)"]
        SSL["SSL / TLS\n(X509 Certs)"]
        SHA["SHA-2 / SHA-3 Auth Provider"]
        ACL["ACL Enforcement"]
        ENFORCE["EnforceAuthentication\nPolicy"]
        KRB["Kerberos Ticket Renewal"]
    end

    %% ── Client Layer ──────────────────────────────────────────────────
    subgraph CLIENT["ZooKeeper Client (confidence: 0.88)"]
        ZKCLIENT["ZooKeeper Client API"]
        HOSTPROV["HostProvider\n(Custom / Selection)"]
        CLIENTCFG["ZKClientConfig"]
        WATCHER["Watcher Interface\n(Event Callbacks)"]
        CNXNSOCK["ClientCnxnSocket\n(NIO)"]
        CHROOT["Chroot Support"]
    end

    %% ── Test Infrastructure ───────────────────────────────────────────
    subgraph TESTINFRA["Test Infrastructure (confidence: 0.92)"]
        CLIENTBASE["ClientBase\n(Base Test Class)"]
        ZKTESTCASE["ZKTestCase\n(Non-parameterized Base)"]
        BLOCKWATCHER["BlockingQueueWatcher\n(Event Capture)"]
        DUMMYWATCHER["DummyWatcher\n(No-op Watcher)"]
        PORTALLOC["PortAssignment\n(Unique Port Allocator)"]
        TESTUTILS["TestUtils\n(Shared Helpers)"]
        METRICSBASE["MetricsProviderCapabilityTest\n(Metrics Base)"]
        METRICSDUMP["MetricsDump\n(Test Metrics Collector)"]
    end

    %% ── Feature / API Tests ───────────────────────────────────────────
    subgraph APITESTS["ZooKeeper API Tests (confidence: 0.91)"]
        EPHEMERALS["GetEphemeralsTest\ngetEphemerals()"]
        CHILDREN["GetAllChildrenNumberTest\ngetAllChildrenNumber()"]
        RMWATCHES["RemoveWatchesCmdTest\nremovewatches cmd"]
        ZKTEST["ZooKeeperTest\nCLI & Core API"]
        CFGWATCHER["ConfigWatcherPathTest\nConfig Watch Path"]
        PERSISTACL["PersistentWatcherACLTest\nPersistent Watches + ACL"]
        EVENTYPE["EventTypeTest\nEvent Type Conversion"]
        ZKUTIL["ZKUtilTest\nUtility Methods"]
    end

    %% ── Session & Connection Tests ────────────────────────────────────
    subgraph SESSIONTESTS["Session & Connection Tests (confidence: 0.89)"]
        SESSIONTIMEOUT["SessionTimeoutTest"]
        SESSIONTEST["SessionTest\nReuse & State Changes"]
        RECONNECT["ClientReconnectTest"]
        CLIENTRETRY["ClientRetryTest"]
        MAXCNXNS["MaxCnxnsTest\nMax Connections"]
        CNXNTEST["ServerCnxnTest"]
        LOCALSES["DuplicateLocalSessionUpgradeTest"]
    end

    %% ── Quorum & Fault Tolerance Tests ───────────────────────────────
    subgraph QUORUMTESTS["Quorum & Fault Tolerance Tests (confidence: 0.87)"]
        QUORUMTEST["QuorumTest"]
        HIERQUORUM["HierarchicalQuorumTest"]
        QUORUMRESTART["QuorumRestartTest"]
        ORACLEQUORUM["QuorumBaseOracle_2Nodes"]
        RECOVERY["RecoveryTest"]
        NONRECOV["NonRecoverableErrorTest"]
        STANDALONE["StandaloneTest"]
        HAMMER["TestHammer\nLoad / Perf Benchmark"]
    end

    %% ── Persistence / Storage Tests ──────────────────────────────────
    subgraph STORAGETESTS["Persistence & Storage Tests (confidence: 0.83)"]
        LOADLOG["LoadFromLogNoServerTest\nTxn Log Replay"]
        DBCORRUPT["ZkDatabaseCorruptionTest"]
        MULTIOP["MultiOperationRecordTest\nSerialization"]
        MULTIRESP["MultiResponseTest\nSerialization"]
        CONNECTREQ["ConnectRequestTest\nProto Serialization"]
    end

    %% ── Auth Tests ────────────────────────────────────────────────────
    subgraph AUTHTESTS["Auth & Security Tests (confidence: 0.90)"]
        KEYAUTH["KeyAuthClientTest"]
        SASLDIGEST["SaslDigestAuthOverSSLTest"]
        SASLKERB["SaslKerberosAuthOverSSLTest"]
        SASLSUPER["SaslSuperUserTest"]
        SASLFAIL["SaslAuthFailDesignatedClientTest"]
        SASLMISSING["SaslAuthMissingClientConfigTest"]
        SASLTEST["SaslAuthTest"]
        ENFORCETEST["EnforceAuthenticationTest"]
        AUTHTEST["AuthTest"]
        X509["X509AuthTest"]
        SHA2TEST["AuthSHA2Test"]
        SHA3TEST["AuthSHA3Test"]
    end

    %% ── Misc Tests ────────────────────────────────────────────────────
    subgraph MISCTESTS["Misc / Infra Tests (confidence: 0.80)"]
        OSMXBEAN["OSMXBeanTest\nSystem Monitoring (JMX)"]
        SERVERARGS["ServerConfigArgTest\nConfig Parsing"]
        NETTYSUITE["NettyNettySuiteTest\nNetty Transport Suite"]
        CANONICALIZE["ClientCanonicalizeTest"]
    end

    %% ── Edges: Infrastructure → Server ───────────────────────────────
    META -->|"versioning"| SERVER
    COMPAT -->|"API diff check"| ZKCLIENT

    %% ── Edges: Server internals ───────────────────────────────────────
    ZKSERVER -->|"manages"| QUORUM
    ZKSERVER -->|"manages"| SESSION
    ZKSERVER -->|"stores data in"| DATASTORE
    DATASTORE -->|"persists via"| TXNLOG
    ZKSERVER -->|"accepts connections via"| CNXN

    %% ── Edges: Auth → Server ──────────────────────────────────────────
    SASL -->|"authenticates to"| ZKSERVER
    SSL -->|"secures transport for"| CNXN
    SHA -->|"auth provider for"| ZKSERVER
    ACL -->|"enforces access on"| DATASTORE
    ENFORCE -->|"policy applied at"| ZKSERVER
    KRB -->|"renews tickets for"| SASL

    %% ── Edges: Client → Server ────────────────────────────────────────
    ZKCLIENT -->|"connects via"| CNXN
    ZKCLIENT -->|"resolves hosts via"| HOSTPROV
    ZKCLIENT -->|"configured by"| CLIENTCFG
    ZKCLIENT -->|"sends events to"| WATCHER
    ZKCLIENT -->|"uses socket"| CNXNSOCK
    ZKCLIENT -->|"namespaces via"| CHROOT

    %% ── Edges: Test Infra → Tests ─────────────────────────────────────
    CLIENTBASE -->|"extended by"| APITESTS
    CLIENTBASE -->|"extended by"| SESSIONTESTS
    CLIENTBASE -->|"extended by"| AUTHTESTS
    ZKTESTCASE -->|"extended by"| QUORUMTESTS
    BLOCKWATCHER -->|"used by"| APITESTS
    DUMMYWATCHER -->|"used by"| SESSIONTESTS
    PORTALLOC -->|"allocates ports for"| QUORUMTESTS
    TESTUTILS -->|"shared helpers for"| AUTHTESTS
    METRICSDUMP -->|"used by"| METRICSBASE

    %% ── Edges: Tests → Server/Client ─────────────────────────────────
    SESSIONTESTS -->|"tests sessions on"| SESSION
    QUORUMTESTS -->|"tests consensus on"| QUORUM
    STORAGETESTS -->|"tests persistence on"| TXNLOG
    AUTHTESTS -->|"tests auth layer"| AUTH
    APITESTS -->|"exercises API on"| ZKCLIENT
    NETTYSUITE -->|"tests transport"| CNXN
    OSMXBEAN -->|"monitors JMX metrics on"| ZKSERVER

    %% ── Edges: SSL used by multiple auth mechanisms ───────────────────
    SASLDIGEST -->|"over SSL"| SSL
    SASLKERB -->|"over SSL"| SSL
    X509 -->|"uses"| SSL
