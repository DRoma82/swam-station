<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  path: { type: String, required: true },
  activeParts: { type: Array, required: true },
  name: { type: String, required: true },
  type: { type: String, required: true },
  depth: { type: Number, default: 0 },
})

const entries = ref([])
const loaded = ref(false)
const expanded = ref(props.type === 'directory' && props.activeParts[props.depth] === props.name)
const href = computed(() => `${props.path}${props.type === 'directory' ? '/' : ''}`)
const isCurrent = computed(() => {
  const activePath = `/${props.activeParts.map(encodeURIComponent).join('/')}`
  return props.path === activePath
})
async function load() {
  if (loaded.value) return
  const response = await fetch(`/api${props.path}/`)
  if (!response.ok) return
  entries.value = (await response.json()).filter((entry) => (
    entry.type === 'directory' ? entry.name.toLowerCase() !== 'assets' : /\.(html|md)$/i.test(entry.name)
  ))
  loaded.value = true
}

async function toggle() {
  expanded.value = !expanded.value
  if (expanded.value) await load()
}

onMounted(() => {
  if (expanded.value) load()
})
</script>

<template>
  <li>
    <div class="tree-item" :class="{ current: isCurrent }">
      <button
        v-if="type === 'directory'"
        type="button"
        class="tree-toggle"
        :aria-label="`${expanded ? 'Collapse' : 'Expand'} ${name}`"
        :aria-expanded="expanded"
        @click="toggle"
      >{{ expanded ? '−' : '+' }}</button>
      <span v-else class="tree-spacer" aria-hidden="true"></span>
      <a :href="href" :aria-current="isCurrent ? 'page' : undefined">{{ name }}</a>
    </div>
    <ul v-if="type === 'directory' && expanded" class="tree-children">
      <TreeExplorer
        v-for="entry in entries"
        :key="entry.name"
        :path="`${path}/${encodeURIComponent(entry.name)}`"
        :active-parts="activeParts"
        :name="entry.name"
        :type="entry.type"
        :depth="depth + 1"
      />
    </ul>
  </li>
</template>
