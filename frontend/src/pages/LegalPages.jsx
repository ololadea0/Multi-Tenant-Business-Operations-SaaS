const privacySections = [
  [
    "1. Information we collect",
    "We may collect account details, business information, usage data and information you choose to provide when you use Daymark or contact us.",
  ],
  [
    "2. How we use information",
    "We use information to provide and improve the service, maintain security, communicate with you and meet legal obligations.",
  ],
  [
    "3. How information is shared",
    "We do not sell personal information. Information may be shared with service providers supporting Daymark, when legally required, or as part of a business transaction.",
  ],
  [
    "4. Data retention",
    "Information is retained only for as long as needed for the purposes described in this policy, including legal, accounting and security requirements.",
  ],
  [
    "5. Your choices",
    "Depending on your location, you may have rights to access, correct, delete or restrict use of your personal information.",
  ],
  [
    "6. Contact",
    "Questions about this policy can be sent to privacy@daymark.example. This contact address is a placeholder.",
  ],
]
const termsSections = [
  [
    "1. Using Daymark",
    "You must provide accurate account information, keep your credentials secure and use the service only in compliance with applicable laws.",
  ],
  [
    "2. Your account and workspace",
    "You are responsible for activity under your account and for ensuring invited team members have appropriate permission to access your workspace.",
  ],
  [
    "3. Your content",
    "You retain ownership of information you submit to Daymark. You grant the permissions needed for us to host, process and display that information to provide the service.",
  ],
  [
    "4. Availability and changes",
    "We work to keep Daymark dependable, but availability is not guaranteed. Features may change as the product develops.",
  ],
  [
    "5. Acceptable use",
    "You may not misuse the service, attempt unauthorised access, disrupt other users or use Daymark to violate the rights of others.",
  ],
  [
    "6. Contact",
    "Questions about these terms can be sent to legal@daymark.example. This contact address is a placeholder.",
  ],
]

export function Privacy() {
  return (
    <Legal
      title="Privacy Policy"
      date="Placeholder policy · Last updated June 2025"
      intro="This placeholder policy explains the types of information Daymark may collect and how that information may be used."
      sections={privacySections}
    />
  )
}
export function Terms() {
  return (
    <Legal
      title="Terms of Service"
      date="Placeholder terms · Last updated June 2025"
      intro="These placeholder terms describe the rules that apply when accessing or using Daymark."
      sections={termsSections}
    />
  )
}

function Legal({
  title,
  date,
  intro,
  sections,
}) {
  return (
    <main className="legal-page">
      <header>
        <span className="eyebrow">DAYMARK / LEGAL</span>
        <h1>{title}</h1>
        <p>{intro}</p>
        <small>{date}</small>
      </header>
      <div className="legal-body">
        <aside>
          On this page
          {sections.map((s) => (
            <a key={s[0]} href={`#${s[0][0]}`}>
              {s[0]}
            </a>
          ))}
        </aside>
        <article>
          {sections.map((s) => (
            <section id={s[0][0]} key={s[0]}>
              <h2>{s[0]}</h2>
              <p>{s[1]}</p>
            </section>
          ))}
          <p className="legal-note">
            This page contains placeholder legal content and must be reviewed by
            qualified legal counsel before publication.
          </p>
        </article>
      </div>
    </main>
  )
}
