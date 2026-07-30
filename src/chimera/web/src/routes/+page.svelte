<script lang="ts">
	import ObjectCard from '$lib/components/ObjectCard.svelte';
	import { connection } from '$lib/stores/connection.svelte';
</script>

<svelte:head><title>chimera — objects</title></svelte:head>

<div class="mb-6 flex items-center justify-between">
	<h1 class="text-xl font-semibold text-slate-100">Objects</h1>
	<button
		class="rounded border border-slate-700 px-3 py-1 text-sm text-slate-300
		       hover:border-slate-500 hover:text-slate-100"
		onclick={() => connection.refresh()}
	>
		Refresh
	</button>
</div>

{#if connection.objects.length === 0}
	<p class="text-sm text-slate-500">
		{connection.status === 'open'
			? 'No objects registered on this server.'
			: 'Waiting for the gateway connection…'}
	</p>
{:else}
	{#each connection.grouped as [cls, objects] (cls)}
		<section class="mb-6">
			<h2 class="mb-2 text-sm font-medium tracking-wide text-slate-400 uppercase">{cls}</h2>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
				{#each objects as object (object.path)}
					<ObjectCard {object} />
				{/each}
			</div>
		</section>
	{/each}
{/if}
