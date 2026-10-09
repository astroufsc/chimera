<script lang="ts">
	import { page } from '$app/state';
	import { onDestroy } from 'svelte';
	import type { ObjectDescription } from 'chimera-ws-client';

	import { client } from '$lib/client';
	import ConfigTable from '$lib/components/ConfigTable.svelte';
	import EventLog, { type LogEntry } from '$lib/components/EventLog.svelte';
	import MethodForm from '$lib/components/MethodForm.svelte';

	const path = $derived('/' + page.params.path);

	let description = $state<ObjectDescription | null>(null);
	let failure = $state<string | null>(null);
	let log = $state<LogEntry[]>([]);
	let subscribed = $state<Record<string, boolean>>({});
	let offs: Record<string, () => void> = {};

	$effect(() => {
		void load(path);
		return unsubscribeAll;
	});

	async function load(p: string) {
		description = null;
		failure = null;
		try {
			description = await client.describe(p);
		} catch (error) {
			failure = String(error);
		}
	}

	function unsubscribeAll() {
		for (const off of Object.values(offs)) off();
		offs = {};
		subscribed = {};
	}

	function toggleEvent(name: string) {
		if (subscribed[name]) {
			offs[name]?.();
			delete offs[name];
			subscribed[name] = false;
			return;
		}
		offs[name] = client.on(path, name, (...args: unknown[]) => {
			log.unshift({ ts: Date.now(), path, event: name, args });
			if (log.length > 500) log.length = 500;
		});
		subscribed[name] = true;
	}

	onDestroy(unsubscribeAll);

	const setConfig = async (key: string, value: unknown) => {
		await client.call(path, '__setitem__', [key, value]);
		await load(path);
	};
</script>

<svelte:head><title>chimera — {path}</title></svelte:head>

{#if failure}
	<div class="rounded border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">
		{failure}
	</div>
{:else if !description}
	<p class="text-sm text-slate-500">Loading {path}…</p>
{:else}
	<div class="mb-6">
		<h1 class="font-mono text-xl text-sky-300">{description.path}</h1>
		<div class="mt-2 flex flex-wrap items-center gap-2">
			<span class="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
				{description.class}
			</span>
			<span class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-400">
				{description.state?.replace('State.', '') ?? 'unknown'}
			</span>
			{#each description.interfaces as iface (iface)}
				<span class="rounded-full bg-violet-500/15 px-2 py-0.5 text-xs text-violet-300">
					{iface}
				</span>
			{/each}
		</div>
	</div>

	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<section>
			<h2 class="mb-2 text-sm font-medium tracking-wide text-slate-400 uppercase">Config</h2>
			<ConfigTable
				config={description.config}
				schema={description.config_schema}
				enums={description.enums}
				onset={setConfig}
			/>
		</section>

		<section>
			<h2 class="mb-2 text-sm font-medium tracking-wide text-slate-400 uppercase">Events</h2>
			{#if Object.keys(description.events).length === 0}
				<p class="text-sm text-slate-500">This object declares no events.</p>
			{:else}
				<div class="mb-3 flex flex-wrap gap-2">
					{#each Object.keys(description.events).sort() as name (name)}
						<button
							class="rounded-full border px-3 py-1 text-xs transition
							       {subscribed[name]
								? 'border-violet-500 bg-violet-500/20 text-violet-200'
								: 'border-slate-700 text-slate-400 hover:border-slate-500'}"
							onclick={() => toggleEvent(name)}
						>
							{name}
						</button>
					{/each}
				</div>
				<EventLog entries={log} onclear={() => (log = [])} />
			{/if}
		</section>
	</div>

	<section class="mt-6">
		<h2 class="mb-2 text-sm font-medium tracking-wide text-slate-400 uppercase">
			Methods <span class="text-slate-600">({Object.keys(description.methods).length})</span>
		</h2>
		<div class="grid grid-cols-1 gap-3">
			{#each Object.keys(description.methods).sort() as name (name)}
				<MethodForm
					{name}
					method={description.methods[name]}
					enums={description.enums}
					oninvoke={(args) => client.call(path, name, args)}
				/>
			{/each}
		</div>
	</section>
{/if}
