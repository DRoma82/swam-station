<script setup>
import MarkdownIt from 'markdown-it'
import { computed, onMounted, ref } from 'vue'
import TreeExplorer from './TreeExplorer.vue'

const entries = ref([])
const treeEntries = ref([])
const markdown = ref('')
const lessonFrame = ref(null)
const loading = ref(true)
const treeLoading = ref(true)
const error = ref('')
const parts = window.location.pathname.split('/').filter(Boolean).map(decodeURIComponent)
const isMarkdown = /\.md$/i.test(parts.at(-1) || '')
const isHtml = /\.html$/i.test(parts.at(-1) || '')
const isPage = isMarkdown || isHtml
const path = `/${parts.map(encodeURIComponent).join('/')}${isPage || !parts.length ? '' : '/'}`
const markdownIt = new MarkdownIt({ html: false, linkify: true, typographer: true })

const breadcrumbs = computed(() => parts.map((name, index) => ({
  name,
  href: `/${parts.slice(0, index + 1).map(encodeURIComponent).join('/')}${index === parts.length - 1 && isPage ? '' : '/'}`,
})))

const folders = computed(() => entries.value.filter(
  (entry) => entry.type === 'directory' && entry.name.toLowerCase() !== 'assets',
))
const pages = computed(() => entries.value.filter(
  (entry) => entry.type === 'file' && /\.(html|md)$/i.test(entry.name),
))
const renderedMarkdown = computed(() => markdownIt.render(markdown.value))

function link(name, directory = false) {
  return `${path}${encodeURIComponent(name)}${directory ? '/' : ''}`
}

function resizeLessonFrame() {
  const frame = lessonFrame.value
  const document = frame?.contentDocument
  if (!frame || !document) return
  frame.style.height = `${document.documentElement.scrollHeight}px`
}

async function loadTree() {
  const response = await fetch('/api/')
  if (!response.ok) return
  treeEntries.value = (await response.json()).filter((entry) => (
    entry.type === 'directory' ? entry.name.toLowerCase() !== 'assets' : /\.(html|md)$/i.test(entry.name)
  ))
}

onMounted(async () => {
  try {
    await loadTree()
  } catch {
    // The page content still works if the optional tree cannot load.
  } finally {
    treeLoading.value = false
  }

  try {
    const response = await fetch(`/api${path}`)
    if (!response.ok) throw new Error(`Request failed (${response.status})`)
    if (isMarkdown) markdown.value = await response.text()
    else if (!isHtml) entries.value = await response.json()
  } catch (cause) {
    error.value = cause.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <details class="tree-panel" open>
        <summary>Browse lessons</summary>
        <nav class="tree" aria-label="Lesson files">
          <ul>
            <li>
              <a class="tree-home" :class="{ current: !parts.length }" href="/" :aria-current="!parts.length ? 'page' : undefined">Home</a>
            </li>
            <TreeExplorer
              v-for="entry in treeEntries"
              :key="entry.name"
              :path="`/${encodeURIComponent(entry.name)}`"
              :active-parts="parts"
              :name="entry.name"
              :type="entry.type"
            />
          </ul>
          <p v-if="treeLoading" class="tree-state">Loading...</p>
        </nav>
      </details>
    </aside>

    <main>
      <section class="intro">
        <nav aria-label="Breadcrumb">
          <a href="/">Home</a>
          <template v-for="crumb in breadcrumbs" :key="crumb.href">
            <span>/</span>
            <a :href="crumb.href">{{ crumb.name }}</a>
          </template>
        </nav>
      </section>

      <p v-if="loading" class="state">Loading lessons...</p>
      <p v-else-if="error" class="state error">Couldn't load this folder. {{ error }}</p>
      <article v-else-if="isMarkdown" class="markdown" v-html="renderedMarkdown"></article>
      <iframe
        v-else-if="isHtml"
        ref="lessonFrame"
        class="lesson-frame"
        :src="`/api${path}`"
        :title="parts.at(-1)"
        @load="resizeLessonFrame"
      ></iframe>
      <p v-else-if="!folders.length && !pages.length" class="state">This folder is empty.</p>

      <template v-else>
        <section v-if="folders.length" aria-labelledby="folders-heading">
          <h2 id="folders-heading">Folders</h2>
          <div class="grid">
            <a v-for="folder in folders" :key="folder.name" class="card" :href="link(folder.name, true)">
              <span class="icon">↗</span>
              <span>{{ folder.name }}</span>
            </a>
          </div>
        </section>

        <section v-if="pages.length" aria-labelledby="pages-heading">
          <h2 id="pages-heading">Pages</h2>
          <div class="pages">
            <a v-for="page in pages" :key="page.name" :href="link(page.name)">{{ page.name }}</a>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>
