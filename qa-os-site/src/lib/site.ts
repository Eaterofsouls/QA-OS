export const site = {
  name: "QA OS",
  tagline: "An architecture for QA reasoning that remembers.",
  domain: "qa.buildwithdaksh.com",
  parentDomain: "buildwithdaksh.com",
  parentUrl: "https://buildwithdaksh.com",
  githubUrl: "https://github.com/Eaterofsouls/QA-OS",
  contactEmail: "me@buildwithdaksh.com",
  author: "Daksh Chauhan",
};

export const navLinks = [
  { href: "/", label: "Home" },
  { href: "/architecture/", label: "Architecture" },
  { href: "/implementation/", label: "Implementation" },
  { href: "/roadmap/", label: "Roadmap" },
  { href: "/run/", label: "Run it" },
  { href: "/#collaborate", label: "Collaborate" },
];

export const heroStatement =
  "Most QA tools store test results. QA OS is trying to build the layer that remembers why — and gets better at reasoning about your product every time a human corrects it.";

export const oneLineThesis =
  "QA OS is an architecture for making organizational quality-engineering reasoning persistent and retrievable, instead of re-derived from scratch by whoever's on call — built independently, with an explicit, honest map of what's real today and what a real QA organization's data and feedback would take it to next.";

// The whole real, working loop — in plain language, five steps, no
// architecture vocabulary required. This is the "explain it simply" version
// of the site; /architecture is the deep version for people who want it.
export const howItWorks = [
  {
    n: "01",
    tag: "INPUT",
    title: "Requirement",
    body: "Someone writes what needs to be true, in plain English — e.g. \u201cUsers must be able to log in via OAuth2, including token refresh and session expiry.\u201d",
  },
  {
    n: "02",
    tag: "AI",
    title: "Risk is scored",
    body: "The system checks its memory for similar requirements it has seen before, then scores how risky this one is \u2014 and writes down why.",
  },
  {
    n: "03",
    tag: "AI",
    title: "Tests are drafted",
    body: "Candidate test cases are generated from the requirement and its risk score. They are marked \u201cdraft.\u201d Nothing here is trusted yet.",
  },
  {
    n: "04",
    tag: "HUMAN",
    title: "A person decides",
    body: "A QA lead approves or rejects each draft. No model makes this call \u2014 this is the one step with no AI in it at all.",
  },
  {
    n: "05",
    tag: "OUTPUT",
    title: "The decision is remembered",
    body: "Whatever the person decided is written back to memory, so the next similar requirement inherits it instead of starting from zero.",
  },
];

export const proofPoints = [
  {
    claim: "Retrieval memory grounded in real human review decisions, not vector-store guessing.",
    status: "IMPLEMENTED" as const,
  },
  {
    claim: "Swappable persistence — in-memory, SQLite, or Neo4j — with zero call-site changes.",
    status: "IMPLEMENTED" as const,
  },
  {
    claim: "Every LLM failure raises a real error; nothing silently fakes success.",
    status: "IMPLEMENTED" as const,
  },
  {
    claim: "Real per-call token and cost accounting, logged to an auditable ledger.",
    status: "IMPLEMENTED" as const,
  },
  {
    claim: "Every module in the repository is labeled by what it actually does — real, partial, or stub — including the ones that are broken or empty. Nothing fake is dressed up as finished.",
    status: "IMPLEMENTED" as const,
  },
];
