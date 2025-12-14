import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import 'katex/dist/katex.min.css'
import { Conversation } from '../api'
import './SearchResults.css'

interface SearchResultsProps {
  results: Conversation[]
}

function SearchResults({ results }: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <div className="no-results">
        <p>No results found. Try a different search query.</p>
      </div>
    )
  }

  return (
    <div className="search-results">
      {results.map((result, index) => (
        <div key={result.message_id} className="result-card">
          <div className="result-header">
            <span className="result-index">#{index + 1}</span>
            <span className={`result-role role-${result.role}`}>{result.role}</span>
            <span className="result-similarity">
              Similarity: {(result.similarity * 100).toFixed(1)}%
            </span>
          </div>
          <div className="result-conversation-id">
            Conversation: {result.conversation_id}
          </div>
          <div className="result-text">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
              components={{
                code({ className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '')
                  const inline = !match
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus as any}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  )
                },
              }}
            >
              {result.text}
            </ReactMarkdown>
          </div>
        </div>
      ))}
    </div>
  )
}

export default SearchResults

