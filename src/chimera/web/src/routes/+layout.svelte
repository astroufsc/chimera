<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { connection } from '$lib/stores/connection.svelte';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		void connection.start();
	});

	const statusStyle = {
		idle: 'bg-slate-700 text-slate-300',
		connecting: 'bg-amber-500/20 text-amber-400',
		open: 'bg-emerald-500/20 text-emerald-400',
		closed: 'bg-red-500/20 text-red-400'
	} as const;
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen">
	<header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
		<nav class="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
			<a href="/" class="text-lg font-semibold tracking-tight text-slate-100">
				chimera
			</a>
			<a href="/" class="text-sm text-slate-400 hover:text-slate-100">Objects</a>
			<a href="/telescope" class="text-sm text-slate-400 hover:text-slate-100">Telescope</a>
			<span class="grow"></span>
			{#if connection.serverInfo.chimera}
				<span class="text-xs text-slate-500">v{connection.serverInfo.chimera}</span>
			{/if}
			<span
				class="rounded-full px-2.5 py-0.5 text-xs font-medium {statusStyle[connection.status]}"
			>
				{connection.status}
			</span>
		</nav>
	</header>

	<main class="mx-auto max-w-5xl px-4 py-6">
		{#if connection.error}
			<div class="mb-4 rounded border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">
				{connection.error}
			</div>
		{/if}
		{@render children()}
	</main>
</div>
